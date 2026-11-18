# SEG-TERM-001 — Correção de integridade dos termos do GATI

## Diagnóstico

A função `public.gati_term_guard()` original verifica transições apenas se `OLD.estado <> 'EM_EDICAO'`. A condição `EXISTS(assinaturas pendentes)` também é falsa quando não existe assinatura alguma. O executor `GATI_Autotestes.py` reproduziu a transição `EM_EDICAO` → `ASSINADO` sem signatários em uma transação isolada com todas as chaves estrangeiras válidas.

## Conteúdo

- `backend/gati/apps/termos/migrations/0004_seg_term_001.py`: migration Django que corrige as transições, exige signatários e impede `INSERT` diretamente em estado final.
- `backend/tests/test_seg_term_001.py`: testes de regressão da operação proibida e do fluxo legítimo de assinatura.
- `GATI_SEGTERM001_AplicarIsolado.py`: aplica somente na base de testes `gati_segterm_teste`, sem ler ou pedir senhas interativamente, utilizando o `.env` existente. **Não aplica ao banco principal.**

## Precauções

1. Use somente em uma cópia local compatível com o código de origem GATI v1.0.0. Não substitua uma migração `0004_*` existente. Confira conflitos e faça backup do código.
2. A migration é propositalmente **irreversível**, pois desfazê-la reintroduziria a vulnerabilidade. Planeje recuperação via novo ajuste/migration e backup.
3. O script de isolamento altera **somente `gati_segterm_teste`**. A base `gati` permanece intocada. Não usa `postgres` superusuário, não altera `pg_hba.conf`, não concede `CREATEDB`.
4. O teste isolado deve concluir sem erros e o executor `GATI_Autotestes.py` deve passar em `SEG-TERM-001` antes de discutir aplicação da migration na base principal.
5. A suíte de regressão foi executada em banco temporário separado: no GitHub Actions, **67 testes aprovados e 2 ignorados** por exigirem ClamAV real; a revisão local documenta 69 testes aprovados. Não conceda CREATEDB permanentemente à conta de aplicação em produção.
6. Um trigger bloqueia operações SQL normais, mas proprietário da tabela ou superusuário podem desabilitá-lo. Em produção, separe ownership/migrations da conta runtime e limite permissões.

## Uso

Os arquivos necessários já estão versionados no repositório: migration, testes e executores individuais. O antigo ZIP de distribuição foi removido por redundância. Para repetir a homologação em uma instalação local **compatível e com dados fictícios**, confira primeiro se a migration já foi aplicada; não a substitua e não rode o executor de promoção em bancos remotos.

Execute no PowerShell, **sem elevar privilégios**:

```powershell
cd "C:\Users\rmdsilva\Projetos\gati"
& ".\backend\.venv\Scripts\python.exe" .\GATI_SEGTERM001_AplicarIsolado.py
& ".\backend\.venv\Scripts\python.exe" .\GATI_Autotestes.py --sem-pytest
```

Resultado esperado do primeiro script: `ISOLADO: MIGRACAO APLICADA`, com confirmação de que a base conectada é `gati_segterm_teste`.

Resultado esperado do segundo: `SEG-TERM-001` aprovado, sem outras falhas novas. Os avisos de servidor web desconectado e da indisponibilidade da suíte pytest são **separados** da correção SQL.

**Situação atual:** a migration `0004_seg_term_001` faz parte da versão publicada e foi aplicada na base local de homologação em 17/11/2026. Em instalações novas, aplique o plano de migrations Django em um banco vazio sob conta de migração autorizada. Em bancos existentes, faça backup, revise o plano e valide a migração em cópia isolada antes da promoção. Os scripts Windows deste documento não são destinados a ambientes cloud.
