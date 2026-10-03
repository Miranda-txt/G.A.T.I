# Aplicação local — arquivos que devem ser removidos nesta DU

**Development Unit:** DU-F0.1-02  
**Motivo:** os arquivos abaixo são workflows vazios/placeholder e já geraram execuções `failure` no GitHub Actions.

Remover localmente pelo explorador do projeto/VS Code antes do commit:

```text
.github/workflows/build-images.yml
.github/workflows/ci-backend.yml
.github/workflows/ci-endpoint.yml
.github/workflows/release.yml
.github/workflows/security.yml
```

Não substituir por workflow fictício.

O CI real deve ser criado em:

```text
DU-F0.5-01 — GitHub Actions inicial
```

Após remover:

1. revisar o diff no GitHub Desktop;
2. confirmar que somente os arquivos planejados foram alterados;
3. não fazer push antes da revisão;
4. após o push manual, solicitar nova leitura do repositório.
