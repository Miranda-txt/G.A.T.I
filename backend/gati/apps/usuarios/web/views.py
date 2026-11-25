import hashlib
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from gati.apps.auditoria.services import audit
from gati.apps.usuarios.permissions import authorize, profile
from gati.common.web import internal

from ..models import LoginFailure, UsuarioTI


@transaction.atomic
def login_view(request):
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    form.fields["username"].label = "Usuário ou e-mail"
    if request.method == "POST":
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        throttle_lock(ip)
        identity = hashlib.sha256(request.POST.get("username", "").strip().casefold().encode()).hexdigest()
        failures = LoginFailure.objects.filter(criado_em__gte=timezone.now() - timedelta(minutes=15), ip=ip)
        blocked = failures.count() >= 30 or failures.filter(identidade_hash=identity).count() >= 5
        if blocked:
            return render(request, "registration/login.html", {"form": form, "blocked": True}, status=429)
        if form.is_valid() and profile(form.get_user()):
            login(request, form.get_user())
            request.session["auth_started"] = timezone.now().timestamp()
            failures.filter(identidade_hash=identity).delete()
            audit(request.user, "LOGIN", ip=ip)
            return redirect("dashboard")
        LoginFailure.objects.create(identidade_hash=identity, ip=ip)
        audit(None, "LOGIN_FALHOU", ip=ip, details={"identificador_hash": identity})
        if not form.errors:
            form.add_error(None, "Credenciais inválidas ou perfil não autorizado.")
    return render(request, "registration/login.html", {"form": form})


def throttle_lock(ip):
    # Serializa a contagem por origem inclusive em múltiplos workers.
    key = int.from_bytes(hashlib.sha256(("gati-auth:" + ip).encode()).digest()[:8], "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])


class ResetRequestView(PasswordResetView):
    html_email_template_name = "registration/password_reset_email_html.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["email"].widget.attrs["class"] = "form-control"
        return form

    @transaction.atomic
    def form_valid(self, form):
        ip = self.request.META.get("REMOTE_ADDR", "127.0.0.1")
        throttle_lock(ip)
        identity = hashlib.sha256(("reset:" + form.cleaned_data["email"].casefold()).encode()).hexdigest()
        recent = LoginFailure.objects.filter(ip=ip, criado_em__gte=timezone.now() - timedelta(minutes=15))
        if recent.count() < 30 and recent.filter(identidade_hash=identity).count() < 3:
            LoginFailure.objects.create(ip=ip, identidade_hash=identity)
            audit(None, "SOLICITAR_REDEFINICAO", ip=ip, details={"identificador_hash": identity})
            return super().form_valid(form)
        return redirect("password_reset_done")


class ResetConfirmView(PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)
        audit(self.user, "REDEFINIR_SENHA", ip=self.request.META.get("REMOTE_ADDR"))
        return response


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        audit(request.user, "LOGOUT", ip=request.META.get("REMOTE_ADDR"))
    logout(request)
    return redirect("login")


@internal
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        audit(user, "ALTERAR_SENHA", ip=request.META.get("REMOTE_ADDR"))
        messages.success(request, "Senha alterada. As demais sessões serão invalidadas.")
        return redirect("dashboard")
    return render(
        request, "records/form.html", {"form": form, "config": {"title": "Alterar senha"}, "resource": ""}
    )


class UserForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    email = forms.EmailField(label="E-mail")
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    perfil = forms.ChoiceField(choices=[("Operador", "Operador"), ("Administrador", "Administrador")])
    senha = forms.CharField(
        label="Senha inicial (mínimo 15 caracteres)", widget=forms.PasswordInput, required=False
    )
    is_active = forms.BooleanField(label="Usuário ativo", required=False, initial=True)


@internal
def users(request):
    authorize(request.user, admin=True)
    return render(
        request,
        "users/list.html",
        {"users": UsuarioTI.objects.prefetch_related("groups").order_by("username")},
    )


@internal
def user_edit(request, pk=None):
    authorize(request.user, admin=True)
    obj = get_object_or_404(UsuarioTI, pk=pk) if pk else None
    initial = (
        {name: getattr(obj, name) for name in ["username", "email", "first_name", "last_name", "is_active"]}
        if obj
        else {}
    )
    if obj:
        initial["perfil"] = profile(obj)
    form = UserForm(request.POST or None, initial=initial)
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
        )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                # Serializa mudanças de administradores para preservar pelo menos um ativo.
                list(
                    UsuarioTI.objects.select_for_update().filter(groups__name="Administrador").order_by("id")
                )
                user = UsuarioTI.objects.select_for_update().get(pk=pk) if pk else UsuarioTI()
                data = form.cleaned_data
                if (
                    obj
                    and user.pk == request.user.pk
                    and (not data["is_active"] or data["perfil"] != "Administrador")
                ):
                    raise ValidationError("Você não pode remover o próprio acesso administrativo.")
                if "@" in data["username"]:
                    raise ValidationError("Use um nome de usuário sem @ para evitar ambiguidade com e-mail.")
                for field in ["username", "email", "first_name", "last_name", "is_active"]:
                    setattr(user, field, data[field])
                if not pk and not data["senha"]:
                    raise ValidationError("Senha inicial obrigatória.")
                if data["senha"]:
                    validate_password(data["senha"], user)
                    user.set_password(data["senha"])
                user.full_clean()
                user.save()
                user.groups.set([Group.objects.get(name=data["perfil"])])
                audit(
                    request.user,
                    "GERENCIAR_USUARIO",
                    user,
                    request.META.get("REMOTE_ADDR"),
                    {"perfil": data["perfil"], "ativo": data["is_active"]},
                )
            return redirect("users")
        except (ValidationError, IntegrityError) as error:
            form.add_error(
                None,
                "; ".join(error.messages)
                if isinstance(error, ValidationError)
                else "Usuário/e-mail já cadastrado.",
            )
    return render(
        request,
        "records/form.html",
        {"form": form, "config": {"title": "Usuários de TI"}, "obj": obj, "resource": ""},
    )


@internal
def audit_view(request):
    from django.core.paginator import Paginator

    from gati.apps.auditoria.models import LogAuditoria

    authorize(request.user, admin=True)
    qs = LogAuditoria.objects.select_related("usuario")
    if request.GET.get("q"):
        qs = qs.filter(
            Q(acao__icontains=request.GET["q"][:100]) | Q(entidade__icontains=request.GET["q"][:100])
        )
    return render(request, "users/audit.html", {"page": Paginator(qs, 50).get_page(request.GET.get("page"))})
