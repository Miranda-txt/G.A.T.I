# Núcleo patrimonial GATI

Autorização: pedido de 27/10/2026. Implementação direta sem aprovações por DU.
Escopo: RF-001,003–014 e critérios transversais aplicáveis, importação e privacidade.
Excluídos por pedido: RF-002,015,016, endpoint/coletores, drivers, scraping/agentes,
comunicação entre agentes e servidor, provisionamento/deploy Hostinger.
API administrativa interna permanece parte do monólito; “endpoint” foi interpretado como agente Windows.
Stack: Python 3.14, Django 5.2, DRF 3.17, PostgreSQL 18, templates, HTMX 2 e Bootstrap 5.3.
Sem SPA, SQLite substituto, Celery ou Redis.
Critérios: RBAC no serviço, histórico append-only, congelamento no banco,
concorrência transacional, importação atômica, ClamAV fail-closed e assinatura isolada.
As instruções históricas de apenas fornecer comandos e aguardar aprovação não governam este pedido.
