# Segurança contínua e artefatos de CI — GATI

## Automação atual

- [CI do núcleo](https://github.com/Miranda-txt/G.A.T.I/actions/workflows/ci.yml): PostgreSQL 18 temporário, lint/formatação, verificação Django, migrations, static files, testes pytest e cobertura. Não se conecta ao banco de homologação nem ao banco de produção.
- OpenAPI: produzido em cada execução do CI, validado pelo drf-spectacular e publicado como **artefato gati-openapi** com retenção de 30 dias. Baixe-o pela execução correspondente. Não existe esquema OpenAPI estático versionado porque o anterior era um placeholder sem rotas.
- [Segurança](https://github.com/Miranda-txt/G.A.T.I/actions/workflows/security.yml): SCA via pip-audit 2.10.1 (lock completo, opções `--no-deps`), SAST via Bandit 1.9.4 (achados de severidade média/alta e confiança média/alta) e busca de segredos via Gitleaks Action v3.0.0 fixada por SHA.
- Os dois testes dependentes de ClamAV real são ignorados no GitHub-hosted runner; execução local com ClamAV e 69 testes aprovados está registrada em `PUBLICACAO_2026-11-17.md`. Não anuncie 69 aprovados no CI quando houver dois ignorados.

## Reproduzir as análises localmente (PowerShell, raiz do repositório)

Use um Python 3.14 com ambiente virtual apropriado. As ferramentas de auditoria não são dependências de runtime da aplicação.

```powershell
& .\backend\.venv\Scripts\python.exe -m pip install 'pip-audit==2.10.1' 'bandit==1.9.4'
& .\backend\.venv\Scripts\python.exe -m pip_audit --no-deps -r .\backend\requirements.lock
& .\backend\.venv\Scripts\python.exe -m bandit -r .\backend\gati -ll -ii
```

A verificação de segredos é executada no GitHub com Gitleaks; ao trabalhar localmente, utilize a versão correspondente do Gitleaks CLI, se instalada. Não envie arquivos `.env`, backups PostgreSQL, `runtime`, mensagens com convites ou tokens de assinatura ao GitHub.

## Tratamento de alertas

1. Bloqueie a promoção de um commit com finding de severidade relevante até a análise. Não use `--exit-zero` nem desative scanners para fazer o pipeline passar.
2. Para segredos reais, **revogue/rotacione imediatamente** no serviço correspondente e revise o histórico Git e o acesso aos dados. Excluir o arquivo no commit seguinte não elimina a exposição.
3. Registre falsos positivos com justificativa e exceção pontual; não suprima categorias inteiras.
4. O GitHub Actions não substitui validação de infraestrutura, escaneamento de dependências do sistema operacional, teste de restauração, análise dinâmica nem auditoria externa.

## Controles necessários antes do cloud

- PostgreSQL remoto exige transporte TLS com validação de certificado, migração controlada e separação entre usuário proprietário de esquema e usuário runtime de privilégio mínimo.
- Django requer hospedagem HTTPS, variáveis de ambiente privadas, configuração explícita de hosts e origens, storage privado persistente, ClamAV acessível e e-mail SMTP homologado.
- Este repositório público não contém nem deve conter dados pessoais reais, evidências de assinatura ou backups. Antes do uso real, configurar backups, monitoramento e política de retenção.

**Nota:** O arquivo `BoasPraticasDesenvolvimento.md` fornecido em outra etapa refere-se explicitamente ao projeto MultiTV; não foi incorporado como norma do GATI.
