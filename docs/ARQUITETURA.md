# Arquitetura implementada

## Dependências e limites

Python 3.14, Django 5.2 LTS, Django REST Framework 3.18.2, PostgreSQL 18. Views e API chamam os mesmos serviços de aplicação. Templates Django renderizam o HTML, HTMX atualiza a pesquisa, Bootstrap 5.3 e CSS local definem a apresentação. Não há SPA, JWT humano, SQLite operacional, coletor, agente Windows ou agendamento de drivers.

As versões instaladas ficam fixadas em `backend/requirements.lock`; `requirements.in` registra as famílias de dependências. `static/vendor` contém Bootstrap e HTMX com seus avisos de licença. As pastas `web`, `api` e `services` dos domínios preservam a organização proposta; a API usa um adaptador compartilhado em `gati/api` para os cadastros de comportamento equivalente, evitando duplicar regras de negócio.

## Modelo e transações

`Ativo` mantém os atributos patrimoniais, categoria, status, localização, garantia e aquisição. `Pessoa` é um responsável patrimonial e não uma conta de acesso. `UsuarioTI` é uma conta interna, vinculada a exatamente um dos grupos Administrador ou Operador. `AtivoTecnico` e `InterfaceRede` preservam somente a separação estrutural prevista; não há edição técnica nem recepção de coleta nesta versão.

`ProcessoMovimentacao` reúne contexto e itens; `Termo` reúne texto, signatários e snapshots. A emissão congela o conteúdo e calcula SHA-256 sobre JSON canônico. `AssinaturaTermo` registra método, identidade congelada, horário, IP, agente e hash aceito. O último aceite finaliza a operação dentro da mesma transação.

Uma entrega cria `ResponsabilidadeAtivo`, muda status para Em Uso, atualiza localização e acrescenta `Movimentacao`. A devolução encerra o vínculo e coloca em estoque ou manutenção. Ativos compartilháveis só mantêm múltiplos responsáveis se a categoria permitir, com localização consistente. Não é possível concluir uma devolução com avaria enquanto restam vínculos de outros responsáveis.

As alterações usam versão otimista e locks PostgreSQL. Aceite, reenvio, confirmação de identidade e cancelamento bloqueiam processo → termo → assinatura → sessão na mesma ordem. Identificadores patrimoniais têm unicidade condicional entre cadastros ativos. Responsabilidades têm restrição parcial e gatilho contra simultaneidade incompatível. Migrations incluem gatilhos para preservar termos, itens, assinaturas, processos encerrados, auditoria, histórico e metadados dos arquivos.

## Decisões do recorte

1. **Autonomia:** a autorização atual dispensa paradas por fase; a documentação anexada continua sendo fonte de arquitetura e regras, não autorização para ações externas.
2. **Infraestrutura:** aplicação e dependências locais foram implementadas; Hostinger, publicação, DNS, TLS do servidor, monitoramento externo e deploy remoto não foram executados.
3. **Termos novos:** o processo cria automaticamente seu primeiro termo. `POST /api/v1/termos/` cria um substituto de um termo cancelado, com `substitui`. Isso evita termos órfãos e duplicidade de termos vigentes.
4. **Correção:** antes da conclusão, um termo cancelado é substituído por novo processo em edição. Depois da conclusão, a substituição é documental, preserva os snapshots da operação e coleta novos aceites sem repetir a movimentação. Alteração real de posse exige nova entrega/devolução. O vínculo `substitui` permite seguir a cadeia de correções.
5. **Contexto do rascunho:** data, destino e observações podem ser editados; tipo e responsável exigem novo processo, para evitar inconsistência entre conferência, ativos e signatários. Texto e itens são revisáveis antes da emissão. Uma edição contextual orienta revisar o texto já resolvido.
6. **Reserva:** emitir termo reserva os ativos contra outras emissões e edições patrimoniais até a conclusão ou cancelamento. O cadastro do responsável pode evoluir, mas a identidade do termo permanece congelada.
7. **Criador inativo:** a conclusão automática por aceite válido não depende de o criador original continuar com conta ativa. A ação conserva sua atribuição histórica; a interface manual continua exigindo autorização atual.
8. **Arquivos:** armazenamento privado em disco; API e interface verificam permissões e hash no download. ClamAV INSTREAM é obrigatório e falha fechada. Importação é síncrona e transacional, com teto de 5.000 linhas.
9. **Privacidade:** documentos aparecem mascarados nas listagens e para operadores na leitura da API. Evidências detalhadas, relatório do titular e desidentificação exigem Administrador. O cadastro mestre pode ser desidentificado após encerramento das finalidades operacionais; evidências históricas retidas não são reescritas.
10. **Sem envio real:** e-mail local em arquivo permite demonstrar convites sem contatar pessoas. SMTP real precisa ser configurado e homologado no ambiente de uso.

## Segurança de aplicação

Autenticação por sessão server-side, Argon2, senha mínima de 15 caracteres, tempo de sessão de 1 hora sem atividade e 12 horas absolutas, bloqueio de tentativas por conta/origem e limite agregado por IP. Redefinição tem token Django de 1 hora, resposta genérica e limitação de solicitações. A sessão de assinatura usa outro cookie: 30 minutos sem atividade, máximo 2 horas. Convite usa 256 bits de aleatoriedade, armazena só hash, expira em 48 horas e é trocado uma vez por POST. A identidade permite até cinco tentativas antes de exigir reemissão.

CSRF protege as operações, inclusive aceite e logout. A interface escapa conteúdo e só resolve tags textuais conhecidas. CSP restringe os recursos à própria aplicação, conteúdo privado usa `no-store`, formulários internos preservam referência de mesma origem. Configuração de produção exige HTTPS e cookies seguros. Superusuário sem perfil funcional não contorna a autorização da aplicação.

## Fontes técnicas consultadas

- [Django 5.2](https://docs.djangoproject.com/en/5.2/) e [proteção CSRF](https://docs.djangoproject.com/en/5.2/ref/csrf/).
- [PostgreSQL — imagem oficial](https://hub.docker.com/_/postgres).
- [ClamAV — versões oficiais](https://www.clamav.net/downloads) e [configuração](https://docs.clamav.net/manual/Usage/Configuration.html).
- [GitHub Actions checkout](https://github.com/actions/checkout) e [setup-python](https://github.com/actions/setup-python).

O código foi validado localmente no Windows. O GitHub Actions foi executado em Ubuntu com PostgreSQL 18 temporário: 67 testes passaram e 2 testes de ClamAV real foram ignorados no runner. A revisão local da publicação registrou 69 testes aprovados com ClamAV. O ambiente Docker local e a hospedagem de produção ainda não foram homologados; consulte `docs/PUBLICACAO_2026-11-17.md` e `docs/SEGURANCA_CI.md`.
