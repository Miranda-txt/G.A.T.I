# Operação do núcleo

## Contas e permissões

Use contas individuais, um grupo funcional por usuário. Administrador gerencia usuários, catálogos, auditoria, cancelamentos e privacidade. Operador mantém ativos, pessoas, manutenções, processos e termos, e edita modelos existentes. Desativar conta impede novo acesso e invalida o uso das sessões existentes. A interface não permite retirar o próprio acesso administrativo.

`bootstrap_gati --admin` prepara o primeiro administrador sem conceder `is_superuser`. O Django Admin genérico não está exposto. Não conceda permissões diretas ou edite grupos por fora do fluxo sem revisar a matriz; a aplicação trabalha com perfis explícitos e nega combinações desconhecidas.

## Rotina

- Atualize as definições ClamAV com FreshClam. No Docker local, o serviço fornece esse processo. O iniciador preparado atualiza antes de iniciar o scanner, se ele estiver parado.
- Execute `python manage.py cleanup_temporarios` pelo menos a cada hora no ambiente de operação. Prévias expiram em 1 hora; resíduos de quarentena antigos são limpos após 24 horas.
- Execute `python manage.py clearsessions` diariamente para sessões Django expiradas. Acesse auditoria apenas quando necessário; os registros podem conter IPs e justificativas.
- Mantenha `runtime/private`, `runtime/emails`, `.env` e backups fora de diretórios públicos e com permissões restritas à conta de serviço/administradores autorizados.
- `/health/live/` confirma o processo web; `/health/ready/` verifica o banco. A disponibilidade do ClamAV é obrigatória para arquivos e deve ser monitorada separadamente com `clamdscan --ping 1`. `/internal/metrics/` fornece somente sinal básico da aplicação, restrito a Administrador.

## Backup e restauração

A hospedagem não foi provisionada. Para uso operacional, configure backup diário consistente de PostgreSQL e arquivos privados, retenção adequada, criptografia e cópia externa conforme a política da organização. Um dump sozinho não contém os anexos.

Procedimento de verificação: suspenda gravações, capture o dump e os arquivos privados do mesmo ponto, registre hashes, restaure em banco/diretório novos e isolados, aplique o código correspondente e compare contagens, vínculos e hashes. Reconcile solicitações de desidentificação posteriores ao backup antes de abrir o acesso. Nunca use dumps reais em desenvolvimento ou testes regulares. Esta entrega não executou restauração de dados produtivos nem criou cronograma remoto de backup.

## Privacidade

O Administrador pode obter o relatório do titular no cadastro da pessoa e registrar desidentificação com justificativa. A aplicação recusa o procedimento quando há responsabilidade ou assinatura pendente. O cadastro mestre perde nome, documento, e-mail, cargo e departamento; o ID técnico e os snapshots históricos retidos permanecem.

Defina a base de tratamento, aviso de privacidade, canal do titular e prazo de retenção no contexto da organização. A aplicação não estabelece prazo legal universal nem decide sozinha o descarte de evidências. A retenção de evidências não permite usar os dados para nova finalidade incompatível.

## Incidentes e falhas previsíveis

| Situação | Resultado e ação |
|---|---|
| Antivírus indisponível | Upload/importação recusados; restabeleça ClamAV e tente novamente. Não há opção de ignorar a verificação. |
| Convite expirado, consumido ou cinco falhas de identidade | Admin/Operador reenvia o convite; tokens e sessões anteriores são revogados. |
| Falha SMTP | O termo continua congelado; confira o transporte e reenvie. |
| Documento congelado com erro | Admin cancela com motivo e cria substituto. O histórico continua disponível. |
| Dado alterado por outro usuário | Recarregue a versão e confira antes de salvar. |
| Conflito após prévia de importação | O lote não é parcialmente criado. Corrija o arquivo e gere nova prévia. |
| Hash do anexo divergente | Download bloqueado; preserve o incidente e recupere a cópia íntegra. |
| Status inválido para entrega ou responsabilidade existente | Faça o fluxo patrimonial correspondente antes de repetir a operação. |

## Homologação antes de uso real

Revisar textos de termos e papéis; configurar HTTPS e proxy confiável; separar usuário de migrations e usuário runtime sem privilégios de dono/superusuário; configurar SMTP; validar atualização de ClamAV e limites do servidor; testar backup/restore; aplicar política de retenção; executar carga representativa e revisão de segurança. Nenhuma dessas tarefas altera o recorte entregue nem autoriza publicação automática.
