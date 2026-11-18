# Rastreabilidade do núcleo

Referência principal: documento consolidado v1.0.0 e anexos de arquitetura, fases, metodologia e contexto. O recorte abaixo aplica a solicitação atual do usuário.

| Requisito | Entrega | Evidência automatizada principal |
|---|---|---|
| RF-001 Inventário | Cadastro, edição com versão, detalhe, inativação, índices únicos parciais | `test_domain.py`, `test_web_api.py` |
| RF-003 Pesquisa | Patrimônio, Service Tag, série, modelo, campos técnicos estruturais, responsável atual, filtros e paginação | `test_web_api.py`, `test_current_filters.py` |
| RF-004 Histórico | Eventos de cadastro, status/localização, entrega/devolução, inativação e retificação aditiva | `test_domain.py`, gatilhos PostgreSQL |
| RF-005 Manutenção | Datas, defeito/serviço, fornecedor, custo, nota fiscal, garantia e anexos | `test_domain.py`, `test_import_files.py` |
| RF-006 Modelos | Criação/inativação Admin, edição Admin/Operador, tags permitidas, sem execução de template | `test_domain.py`, `test_web_api.py` |
| RF-007 Entrega | Wizard de sete etapas, múltiplos ativos, conferência, signatários, conclusão após todos os aceites | `test_domain.py`, `test_web_api.py`, navegador |
| RF-008 Devolução | Conferência, avarias/divergências, encerramento dos vínculos, estoque/manutenção | `test_domain.py` |
| RF-009 Assinatura e-mail | Convite único, hash, 48h, troca por sessão, identidade, reenvio e erro SMTP seguro | `test_signatures.py` (transporte de e-mail de teste) |
| RF-010 Presencial | Logout administrativo, sessão separada, confirmação da identidade e aceite explícito | `test_signatures.py`, navegador |
| RF-011 Arquivos | PDF/JPEG/PNG, limites, inspeção, ClamAV, privado, hash e download autorizado | `test_import_files.py`, `test_scanner_live.py` |
| RF-012 Pessoas | Cadastro mínimo, vínculo atual/histórico, documento mascarado, inativação e desidentificação | `test_domain.py`, `test_web_api.py` |
| RF-013 Painel | Distribuição por status, garantias e termos pendentes | `test_web_api.py`, captura de navegador |
| RF-014 Termos individuais | Texto e itens em edição, snapshots e congelamento, cancelamento motivado e substituição | `test_domain.py`, `test_integrity_extra.py` |
| DEC-022 Importação | CSV/XLSX, prévia/confirmar, criação somente, validação integral, lote atômico, limpeza | `test_import_files.py`, `test_scanner_live.py` |
| RNF-001/002/008 | Sessão, senha, Argon2, limitação de tentativas, matriz Admin/Operador | `test_signatures.py`, `test_web_api.py` |
| RNF-004/005 | Auditoria e evidências imutáveis na aplicação e no banco | `test_domain.py`, `test_integrity_extra.py` |
| RNF-010 | Interface de desktop, notebook e tablet, tabelas com rolagem local | Evidências em `docs/evidencias` |
| RNF-011 / DEC-023 | Minimização, mascaramento, finalidade operacional, relatório e desidentificação | `test_domain.py`; operação descrita em `OPERACAO.md` |
| Qualidade Python | Testes em PostgreSQL, cobertura de linhas/ramificações, lint, migrations, esquema | `VALIDACAO.md`, `.github/workflows/ci.yml` |

RF-002, RF-015, RF-016, agentes, Endpoint, enrollment, telemetria, atualização de drivers e toda comunicação associada estão fora do recorte. RNF de disponibilidade, backup de infraestrutura e desempenho em staging representativo dependem do ambiente de hospedagem excluído; não são declarados homologados por esta entrega local.

As provas de segurança implementadas não equivalem a uma auditoria externa integral OWASP ASVS L2/ZAP. O envio SMTP real e a política organizacional de retenção também dependem da configuração de operação.
