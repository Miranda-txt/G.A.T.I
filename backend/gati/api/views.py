from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from gati.apps.arquivos.models import Arquivo
from gati.apps.arquivos.services import download_file, upload_file
from gati.apps.ativos.models import Ativo
from gati.apps.auditoria.models import LogAuditoria
from gati.apps.cadastros.models import Localizacao
from gati.apps.movimentacoes.models import Movimentacao, ProcessoMovimentacao, ResponsabilidadeAtivo
from gati.apps.movimentacoes.services import complete_process, create_process, edit_process
from gati.apps.pessoas.models import Pessoa
from gati.apps.termos.models import AssinaturaTermo, ModeloTermo, Termo
from gati.apps.termos.services import (
    cancel,
    edit_draft,
    edit_items,
    issue,
    replace_cancelled,
    send_invitation,
)
from gati.apps.usuarios.permissions import AdminPermission, is_admin
from gati.common.catalog import inactivate, save_record
from gati.common.registry import RESOURCES
from gati.common.selectors import records


class StrictSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if set(data) - set(self.fields):
            raise serializers.ValidationError("Há campos desconhecidos.")
        for key in data:
            if self.fields[key].read_only:
                raise serializers.ValidationError({key: "Campo somente leitura."})
        return super().to_internal_value(data)


def serializer_for(config):
    field_names = ["id", *config.fields, "versao", "criado_em", "atualizado_em"]
    if "ativo" not in field_names and hasattr(config.model, "ativo"):
        field_names.append("ativo")
    readonly = ["id", "criado_em", "atualizado_em"] + (
        ["ativo"] if "ativo" not in config.fields and "ativo" in field_names else []
    )
    meta = type("Meta", (), {"model": config.model, "fields": field_names, "read_only_fields": readonly})

    def representation(self, obj):
        result = serializers.ModelSerializer.to_representation(self, obj)
        if isinstance(obj, Pessoa) and not is_admin(self.context["request"].user):
            result["documento"] = obj.documento_mascarado
        return result

    return type(
        config.model.__name__ + "Serializer",
        (StrictSerializer,),
        {"Meta": meta, "to_representation": representation},
    )


class RecordViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    resource = ""

    def get_queryset(self):
        allowed = {
            "q",
            "situacao",
            "status",
            "categoria",
            "localizacao",
            "responsavel",
            "departamento",
            "garantia",
            "ordering",
            "page",
            "page_size",
            "format",
        }
        if set(self.request.query_params) - allowed:
            raise ValidationError("Filtro desconhecido.")
        return records(self.resource, RESOURCES[self.resource].model, self.request.query_params)

    def get_serializer_class(self):
        return serializer_for(RESOURCES[self.resource])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("versao", None)
        obj = save_record(
            request.user, RESOURCES[self.resource].model, data, ip=request.META.get("REMOTE_ADDR")
        )
        return Response(self.get_serializer(obj).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        version = data.pop("versao", None)
        saved = save_record(request.user, type(obj), data, obj.pk, version, request.META.get("REMOTE_ADDR"))
        return Response(self.get_serializer(saved).data)

    @action(detail=True, methods=["post"])
    def inativar(self, request, pk=None):
        obj = self.get_object()
        if not isinstance(getattr(obj, "ativo", None), bool):
            raise ValidationError("Inativação indisponível para esta entidade.")
        version = serializers.IntegerField(min_value=1).run_validation(request.data.get("versao"))
        saved = inactivate(request.user, obj, version, request.META.get("REMOTE_ADDR"))
        return Response(self.get_serializer(saved).data)

    @action(detail=True, methods=["post"])
    def arquivos(self, request, pk=None):
        if len(request.FILES) != 1 or "arquivo" not in request.FILES:
            raise ValidationError("Envie um único arquivo.")
        obj = upload_file(
            request.user, request.FILES["arquivo"], self.get_object(), request.META.get("REMOTE_ADDR")
        )
        return Response({"id": obj.pk, "sha256": obj.sha256, "tamanho": obj.tamanho}, status=201)


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimentacao
        fields = ["id", "ativo", "usuario", "processo", "data", "tipo", "descricao", "antes", "depois"]


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movimentacao.objects.all()
    serializer_class = HistorySerializer


class ResponsibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsabilidadeAtivo
        fields = ["id", "ativo", "pessoa", "inicio", "fim", "processo_inicio", "processo_fim"]


class ResponsibilityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResponsabilidadeAtivo.objects.order_by("-inicio")
    serializer_class = ResponsibilitySerializer


class ItemInput(serializers.Serializer):
    ativo = serializers.PrimaryKeyRelatedField(queryset=Ativo.objects.filter(ativo=True))
    acessorios = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    condicoes = serializers.CharField(max_length=4000)
    avaria = serializers.BooleanField(default=False)
    divergencias = serializers.CharField(required=False, allow_blank=True, max_length=4000)


class SignerInput(serializers.Serializer):
    pessoa = serializers.PrimaryKeyRelatedField(queryset=Pessoa.objects.filter(ativo=True))
    papel = serializers.ChoiceField(choices=["RESPONSAVEL", "TESTEMUNHA", "ACOMPANHANTE"])
    metodo = serializers.ChoiceField(choices=["EMAIL", "PRESENCIAL"])


class ProcessInput(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["ENTREGA", "DEVOLUCAO"])
    responsavel = serializers.PrimaryKeyRelatedField(queryset=Pessoa.objects.filter(ativo=True))
    localizacao = serializers.PrimaryKeyRelatedField(queryset=Localizacao.objects.filter(ativo=True))
    data = serializers.DateField()
    observacoes = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    modelo = serializers.PrimaryKeyRelatedField(queryset=ModeloTermo.objects.filter(ativo=True))
    itens = ItemInput(many=True)
    signatarios = SignerInput(many=True)

    def to_internal_value(self, data):
        if set(data) - set(self.fields):
            raise serializers.ValidationError("Campo não permitido.")
        return super().to_internal_value(data)


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessoMovimentacao
        fields = [
            "id",
            "tipo",
            "responsavel",
            "localizacao",
            "data",
            "observacoes",
            "estado",
            "versao",
            "concluido_em",
        ]


class ProcessViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProcessoMovimentacao.objects.all()
    serializer_class = ProcessSerializer

    @extend_schema(
        request=inline_serializer(
            name="ProcessPatch",
            fields={
                "localizacao": serializers.IntegerField(required=False),
                "data": serializers.DateField(required=False),
                "observacoes": serializers.CharField(required=False, allow_blank=True),
                "versao": serializers.IntegerField(),
            },
        )
    )
    def partial_update(self, request, pk=None):
        if set(request.data) - {"localizacao", "data", "observacoes", "versao"}:
            raise ValidationError("Campo não permitido.")
        serializer = ProcessInput(data=request.data, partial=True)
        # Versão é controle de concorrência, fora do contexto do processo.
        serializer.initial_data = {k: v for k, v in request.data.items() if k != "versao"}
        serializer.is_valid(raise_exception=True)
        version = serializers.IntegerField(min_value=1).run_validation(request.data.get("versao"))
        obj = edit_process(
            request.user,
            self.get_object(),
            serializer.validated_data,
            version,
            request.META.get("REMOTE_ADDR"),
        )
        return Response(self.get_serializer(obj).data)

    @extend_schema(request=ProcessInput, responses={201: ProcessSerializer})
    def create(self, request):
        serializer = ProcessInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("itens")
        signers = data.pop("signatarios")
        model = data.pop("modelo")
        obj = create_process(request.user, data, items, model, signers, request.META.get("REMOTE_ADDR"))
        return Response(ProcessSerializer(obj).data, status=201)

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        obj = complete_process(request.user, self.get_object(), request.META.get("REMOTE_ADDR"))
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def arquivos(self, request, pk=None):
        if len(request.FILES) != 1 or "arquivo" not in request.FILES:
            raise ValidationError("Envie um arquivo.")
        obj = upload_file(
            request.user, request.FILES["arquivo"], self.get_object(), request.META.get("REMOTE_ADDR")
        )
        return Response({"id": obj.pk, "sha256": obj.sha256}, status=201)


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termo
        fields = [
            "id",
            "processo",
            "modelo",
            "texto",
            "estado",
            "sha256",
            "emitido_em",
            "cancelado_em",
            "motivo_cancelamento",
            "versao",
            "substitui",
        ]


class TermViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Termo.objects.all()
    serializer_class = TermSerializer

    @extend_schema(
        request=inline_serializer(name="TermReplacement", fields={"substitui": serializers.IntegerField()}),
        responses={201: TermSerializer},
    )
    def create(self, request):
        from django.shortcuts import get_object_or_404

        if set(request.data) != {"substitui"}:
            raise ValidationError(
                "Novos termos nascem no processo. Para correção, informe somente substitui (ID do termo cancelado)."
            )
        pk = serializers.IntegerField(min_value=1).run_validation(request.data["substitui"])
        term = replace_cancelled(
            request.user, get_object_or_404(Termo, pk=pk), request.META.get("REMOTE_ADDR")
        )
        return Response(self.get_serializer(term).data, status=201)

    @extend_schema(
        request=inline_serializer(
            name="TermItemsPatch",
            fields={
                "itens": ItemInput(many=True),
                "signatarios": SignerInput(many=True),
                "versao": serializers.IntegerField(),
            },
        )
    )
    @action(detail=True, methods=["patch"])
    def itens(self, request, pk=None):
        if set(request.data) != {"itens", "signatarios", "versao"}:
            raise ValidationError("Informe itens, signatarios e versao.")
        items = ItemInput(data=request.data["itens"], many=True)
        signers = SignerInput(data=request.data["signatarios"], many=True)
        items.is_valid(raise_exception=True)
        signers.is_valid(raise_exception=True)
        version = serializers.IntegerField(min_value=1).run_validation(request.data["versao"])
        term = edit_items(
            request.user,
            self.get_object(),
            items.validated_data,
            signers.validated_data,
            version,
            request.META.get("REMOTE_ADDR"),
        )
        return Response(self.get_serializer(term).data)

    @extend_schema(
        request=inline_serializer(
            name="TermTextPatch",
            fields={"texto": serializers.CharField(), "versao": serializers.IntegerField()},
        )
    )
    def partial_update(self, request, pk=None):
        if set(request.data) - {"texto", "versao"}:
            raise ValidationError("Campo não permitido.")
        text = serializers.CharField(max_length=30000).run_validation(request.data.get("texto"))
        version = serializers.IntegerField(min_value=1).run_validation(request.data.get("versao"))
        term = edit_draft(
            request.user,
            self.get_object(),
            text,
            version,
            request.META.get("REMOTE_ADDR"),
        )
        return Response(self.get_serializer(term).data)

    @action(detail=True, methods=["post"], url_path="emitir-para-assinatura")
    def emitir(self, request, pk=None):
        term = issue(request.user, self.get_object(), request.META.get("REMOTE_ADDR"))
        return Response(self.get_serializer(term).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        reason = serializers.CharField(min_length=10, max_length=2000).run_validation(
            request.data.get("motivo")
        )
        term = cancel(request.user, self.get_object(), reason, request.META.get("REMOTE_ADDR"))
        return Response(self.get_serializer(term).data)


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAuditoria
        fields = ["id", "usuario", "data", "acao", "entidade", "objeto_id", "ip", "detalhes"]


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AdminPermission]
    queryset = LogAuditoria.objects.all()
    serializer_class = AuditSerializer


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssinaturaTermo
        fields = ["id", "termo", "pessoa", "papel", "metodo", "assinado_em", "hash_assinado"]


class SignatureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssinaturaTermo.objects.all().order_by("id")
    serializer_class = SignatureSerializer

    @action(detail=True, methods=["post"])
    def reenviar(self, request, pk=None):
        send_invitation(request.user, self.get_object(), request.META.get("REMOTE_ADDR"))
        return Response({"status": "submetido"})

    @action(detail=True, methods=["post"], url_path="iniciar-presencial")
    def presencial(self, request, pk=None):
        from gati.apps.termos.web.views import signature_action

        return signature_action(request._request, int(pk), "presencial")


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Arquivo
        fields = [
            "id",
            "nome_original",
            "mime",
            "tamanho",
            "sha256",
            "ativo_vinculado",
            "manutencao",
            "processo",
            "ativo",
        ]


class FileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Arquivo.objects.all().order_by("-id")
    serializer_class = FileSerializer

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        from django.http import FileResponse

        obj = self.get_object()
        return FileResponse(
            download_file(request.user, obj, request.META.get("REMOTE_ADDR")),
            as_attachment=True,
            filename=obj.nome_original,
            content_type=obj.mime,
        )
