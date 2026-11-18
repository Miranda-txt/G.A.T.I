from dataclasses import dataclass

from django.apps import apps


@dataclass(frozen=True)
class Resource:
    label: str
    title: str
    singular: str
    fields: tuple
    columns: tuple
    admin: bool = False

    @property
    def model(self):
        return apps.get_model(self.label)


RESOURCES = {
    "ativos": Resource(
        "ativos.Ativo",
        "Inventário",
        "ativo",
        (
            "patrimonio",
            "service_tag",
            "numero_serie",
            "categoria",
            "fabricante",
            "modelo",
            "localizacao",
            "status",
            "data_aquisicao",
            "valor_aquisicao",
            "nota_fiscal",
            "garantia_fim",
            "observacoes",
        ),
        (
            ("patrimonio", "Patrimônio"),
            ("modelo", "Equipamento"),
            ("categoria", "Categoria"),
            ("status", "Status"),
            ("localizacao", "Localização"),
        ),
    ),
    "pessoas": Resource(
        "pessoas.Pessoa",
        "Pessoas",
        "pessoa",
        ("nome", "documento", "departamento", "cargo", "email"),
        (
            ("nome", "Nome"),
            ("documento_mascarado", "Documento"),
            ("departamento", "Departamento"),
            ("cargo", "Cargo"),
        ),
    ),
    "manutencoes": Resource(
        "manutencoes.Manutencao",
        "Manutenções",
        "manutenção",
        (
            "ativo",
            "data_inicio",
            "data_fim",
            "fornecedor",
            "nota_fiscal",
            "defeito",
            "servico",
            "custo",
            "em_garantia",
        ),
        (
            ("ativo", "Ativo"),
            ("data_inicio", "Início"),
            ("fornecedor", "Fornecedor"),
            ("data_fim", "Conclusão"),
            ("custo", "Custo (R$)"),
        ),
    ),
    "modelos-termo": Resource(
        "termos.ModeloTermo",
        "Modelos de termo",
        "modelo",
        ("nome", "texto"),
        (("nome", "Modelo"), ("versao", "Versão"), ("ativo", "Ativo")),
    ),
    "departamentos": Resource(
        "cadastros.Departamento",
        "Departamentos",
        "departamento",
        ("nome",),
        (("nome", "Departamento"), ("ativo", "Ativo")),
        True,
    ),
    "categorias-ativos": Resource(
        "cadastros.CategoriaAtivo",
        "Categorias de ativo",
        "categoria",
        ("nome", "multiplos_responsaveis"),
        (("nome", "Categoria"), ("multiplos_responsaveis", "Compartilhado"), ("ativo", "Ativo")),
        True,
    ),
    "localizacoes": Resource(
        "cadastros.Localizacao",
        "Localizações",
        "localização",
        ("nome", "descricao"),
        (("nome", "Localização"), ("descricao", "Descrição"), ("ativo", "Ativo")),
        True,
    ),
    "status-ativos": Resource(
        "cadastros.StatusAtivo",
        "Status dos ativos",
        "status",
        ("nome", "codigo"),
        (("nome", "Status"), ("codigo", "Código"), ("ativo", "Ativo")),
        True,
    ),
}
