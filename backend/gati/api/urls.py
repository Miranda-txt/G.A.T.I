from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter

from .views import (
    RESOURCES,
    AuditViewSet,
    FileViewSet,
    HistoryViewSet,
    ProcessViewSet,
    RecordViewSet,
    ResponsibilityViewSet,
    SignatureViewSet,
    TermViewSet,
    serializer_for,
)

router = DefaultRouter()
for key, config in RESOURCES.items():
    view = type(
        config.model.__name__ + "ViewSet",
        (RecordViewSet,),
        {"resource": key, "queryset": config.model.objects.all(), "serializer_class": serializer_for(config)},
    )
    router.register(key, view, basename=key)
for key, view in [
    ("movimentacoes", HistoryViewSet),
    ("responsabilidades-ativos", ResponsibilityViewSet),
    ("processos-movimentacao", ProcessViewSet),
    ("termos", TermViewSet),
    ("logs-auditoria", AuditViewSet),
    ("assinaturas-termo", SignatureViewSet),
    ("arquivos", FileViewSet),
]:
    router.register(key, view, basename=key)
urlpatterns = [path("schema/", SpectacularAPIView.as_view(api_version="v1"), name="schema"), path("", include(router.urls))]
