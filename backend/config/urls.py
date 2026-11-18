from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.urls import include, path

from gati.apps.dashboard.web.views import dashboard
from gati.apps.importacoes.web import views as imports
from gati.apps.movimentacoes.web import views as movements
from gati.apps.termos.web import views as terms
from gati.apps.usuarios.permissions import authorize
from gati.apps.usuarios.web import views as users
from gati.common import web
from gati.observability import health


@web.internal
def settings_view(request):
    authorize(request.user, admin=True)
    return render(
        request,
        "users/settings.html",
        {"catalogs": [(k, v.title) for k, v in web.RESOURCES.items() if v.admin]},
    )


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("entrar/", users.login_view, name="login"),
    path("sair/", users.logout_view, name="logout"),
    path("senha/alterar/", users.password_change, name="password_change"),
    path(
        "senha/recuperar/",
        users.ResetRequestView.as_view(),
        name="password_reset",
    ),
    path("senha/recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        users.ResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("senha/redefinida/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("cadastros/<slug:resource>/", web.listing, name="listing"),
    path("cadastros/<slug:resource>/novo/", web.edit, name="create"),
    path("cadastros/<slug:resource>/<int:pk>/", web.detail, name="detail"),
    path("cadastros/<slug:resource>/<int:pk>/editar/", web.edit, name="edit"),
    path("cadastros/<slug:resource>/<int:pk>/inativar/", web.deactivate, name="deactivate"),
    path("cadastros/<slug:resource>/<int:pk>/arquivos/", web.upload, name="upload"),
    path("arquivos/<int:pk>/download/", web.download, name="download"),
    path("arquivos/<int:pk>/inativar/", web.file_deactivate, name="file_deactivate"),
    path("pessoas/<int:pk>/desidentificar/", web.deidentify_view, name="deidentify"),
    path("pessoas/<int:pk>/relatorio/", web.privacy_report, name="privacy_report"),
    path("ativos/<int:pk>/retificar/", web.history_correction, name="history_correction"),
    path("processos/", movements.process_list, name="process_list"),
    path("processos/novo/<int:step>/", movements.wizard, name="wizard"),
    path("processos/<int:pk>/", movements.process_detail, name="process_detail"),
    path("processos/<int:pk>/editar/", movements.process_edit, name="process_edit"),
    path("termos/", terms.term_list, name="term_list"),
    path("termos/<int:pk>/", terms.term_detail, name="term_detail"),
    path("termos/<int:pk>/itens/", terms.term_items, name="term_items"),
    path("termos/<int:pk>/<slug:action>/", terms.term_action, name="term_action"),
    path("assinaturas/<int:pk>/<slug:action>/", terms.signature_action, name="signature_action"),
    path("assinar/iniciar/", terms.sign_start, name="sign_start"),
    path("assinar/", terms.sign_view, name="sign_view"),
    path("assinar/confirmar-identidade/", terms.sign_identity, name="sign_identity"),
    path("assinar/aceitar/", terms.sign_accept, name="sign_accept"),
    path("importar/<slug:kind>/", imports.import_view, name="import"),
    path("importar/<slug:kind>/modelo/", imports.template, name="import_template"),
    path("importacoes/<uuid:pk>/", imports.preview_view, name="import_preview"),
    path("usuarios/", users.users, name="users"),
    path("usuarios/novo/", users.user_edit, name="user_create"),
    path("usuarios/<int:pk>/", users.user_edit, name="user_edit"),
    path("auditoria/", users.audit_view, name="audit"),
    path("configuracoes/", settings_view, name="settings"),
    path("api/v1/", include(("gati.api.urls", "api"), namespace="v1")),
    path("health/live/", health.live),
    path("health/ready/", health.ready),
    path("internal/metrics/", health.metrics),
]
