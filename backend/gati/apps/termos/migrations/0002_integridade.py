from django.db import migrations

SQL = r"""
CREATE FUNCTION gati_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Registro historico imutavel' USING ERRCODE='23514'; END $$;
CREATE TRIGGER historico_imutavel BEFORE UPDATE OR DELETE ON movimentacoes_movimentacao
FOR EACH ROW EXECUTE FUNCTION gati_append_only();
CREATE TRIGGER auditoria_imutavel BEFORE UPDATE OR DELETE ON auditoria_logauditoria
FOR EACH ROW EXECUTE FUNCTION gati_append_only();

CREATE FUNCTION gati_term_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Termo nao pode ser excluido' USING ERRCODE='23514'; END IF;
 IF OLD.estado <> 'EM_EDICAO' THEN
  IF (to_jsonb(NEW) - ARRAY['estado','versao','atualizado_em','cancelado_em','motivo_cancelamento'])
    IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['estado','versao','atualizado_em','cancelado_em','motivo_cancelamento']) THEN
   RAISE EXCEPTION 'Conteudo congelado' USING ERRCODE='23514';
  END IF;
  IF OLD.estado='CANCELADO' AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
   RAISE EXCEPTION 'Cancelamento imutavel' USING ERRCODE='23514';
  END IF;
  IF NEW.estado <> OLD.estado AND NOT
    (OLD.estado='AGUARDANDO_ASSINATURAS' AND NEW.estado IN ('ASSINADO','CANCELADO') OR
     OLD.estado='ASSINADO' AND NEW.estado='CANCELADO') THEN
   RAISE EXCEPTION 'Transicao invalida' USING ERRCODE='23514';
  END IF;
 END IF;
 IF NEW.estado='ASSINADO' AND EXISTS(SELECT 1 FROM termos_assinaturatermo WHERE termo_id=NEW.id AND assinado_em IS NULL) THEN
  RAISE EXCEPTION 'Faltam assinaturas' USING ERRCODE='23514';
 END IF;
 IF NEW.estado='CANCELADO' AND (NEW.cancelado_em IS NULL OR length(NEW.motivo_cancelamento)<10) THEN
  RAISE EXCEPTION 'Cancelamento exige motivo' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER termo_congelado BEFORE UPDATE OR DELETE ON termos_termo
FOR EACH ROW EXECUTE FUNCTION gati_term_guard();

CREATE FUNCTION gati_item_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_estado text; parent_id bigint;
BEGIN
 IF TG_OP='DELETE' THEN parent_id=OLD.termo_id; ELSE parent_id=NEW.termo_id; END IF;
 SELECT estado INTO parent_estado FROM termos_termo WHERE id=parent_id FOR UPDATE;
 IF parent_estado <> 'EM_EDICAO' THEN RAISE EXCEPTION 'Item congelado' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND NEW.termo_id<>OLD.termo_id THEN
  SELECT estado INTO parent_estado FROM termos_termo WHERE id=OLD.termo_id;
  IF parent_estado <> 'EM_EDICAO' THEN RAISE EXCEPTION 'Item congelado' USING ERRCODE='23514'; END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER item_congelado BEFORE INSERT OR UPDATE OR DELETE ON termos_termoitem
FOR EACH ROW EXECUTE FUNCTION gati_item_guard();

CREATE FUNCTION gati_signature_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE term_estado text; term_hash text; parent_id bigint;
BEGIN
 IF TG_OP='DELETE' THEN parent_id=OLD.termo_id; ELSE parent_id=NEW.termo_id; END IF;
 SELECT estado,sha256 INTO term_estado,term_hash FROM termos_termo WHERE id=parent_id FOR UPDATE;
 IF TG_OP='INSERT' OR TG_OP='DELETE' THEN
  IF term_estado<>'EM_EDICAO' THEN RAISE EXCEPTION 'Signatario congelado' USING ERRCODE='23514'; END IF;
 ELSE
  IF OLD.assinado_em IS NOT NULL AND to_jsonb(OLD) IS DISTINCT FROM to_jsonb(NEW) THEN
   RAISE EXCEPTION 'Assinatura imutavel' USING ERRCODE='23514';
  END IF;
  IF term_estado<>'EM_EDICAO' AND
   (NEW.termo_id,NEW.pessoa_id,NEW.papel,NEW.metodo,NEW.snapshot) IS DISTINCT FROM
   (OLD.termo_id,OLD.pessoa_id,OLD.papel,OLD.metodo,OLD.snapshot) THEN
   RAISE EXCEPTION 'Signatario congelado' USING ERRCODE='23514';
  END IF;
  IF NEW.termo_id<>OLD.termo_id AND EXISTS(SELECT 1 FROM termos_termo WHERE id=OLD.termo_id AND estado<>'EM_EDICAO') THEN
   RAISE EXCEPTION 'Assinatura congelada' USING ERRCODE='23514';
  END IF;
  IF OLD.assinado_em IS NULL AND NEW.assinado_em IS NOT NULL AND
    (term_estado<>'AGUARDANDO_ASSINATURAS' OR NEW.hash_assinado<>term_hash) THEN
   RAISE EXCEPTION 'Aceite invalido' USING ERRCODE='23514';
  END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER assinatura_protegida BEFORE INSERT OR UPDATE OR DELETE ON termos_assinaturatermo
FOR EACH ROW EXECUTE FUNCTION gati_signature_guard();

CREATE FUNCTION gati_process_item_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_estado text; parent_id bigint;
BEGIN
 IF TG_OP='DELETE' THEN parent_id=OLD.processo_id; ELSE parent_id=NEW.processo_id; END IF;
 SELECT estado INTO parent_estado FROM movimentacoes_processomovimentacao WHERE id=parent_id FOR UPDATE;
 IF parent_estado<>'EM_EDICAO' THEN RAISE EXCEPTION 'Processo congelado' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND NEW.processo_id<>OLD.processo_id THEN
  IF EXISTS(SELECT 1 FROM movimentacoes_processomovimentacao WHERE id=OLD.processo_id AND estado<>'EM_EDICAO') THEN
   RAISE EXCEPTION 'Processo congelado' USING ERRCODE='23514';
  END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER processo_item_protegido BEFORE INSERT OR UPDATE OR DELETE ON movimentacoes_processoitem
FOR EACH ROW EXECUTE FUNCTION gati_process_item_guard();

CREATE FUNCTION gati_process_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Use cancelamento' USING ERRCODE='23514'; END IF;
 IF OLD.estado<>'EM_EDICAO' AND
  (to_jsonb(NEW)-ARRAY['estado','concluido_em','versao','atualizado_em']) IS DISTINCT FROM
  (to_jsonb(OLD)-ARRAY['estado','concluido_em','versao','atualizado_em']) THEN
  RAISE EXCEPTION 'Contexto congelado' USING ERRCODE='23514';
 END IF;
 IF OLD.estado IN ('CANCELADO','CONCLUIDO') AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
  RAISE EXCEPTION 'Processo encerrado' USING ERRCODE='23514';
 END IF;
 IF NEW.estado='CONCLUIDO' AND NOT EXISTS(SELECT 1 FROM termos_termo WHERE processo_id=NEW.id AND estado='ASSINADO') THEN
  RAISE EXCEPTION 'Termo assinado obrigatorio' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER processo_protegido BEFORE UPDATE OR DELETE ON movimentacoes_processomovimentacao
FOR EACH ROW EXECUTE FUNCTION gati_process_guard();

CREATE FUNCTION gati_responsibility_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE multi boolean;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Responsabilidade historica' USING ERRCODE='23514'; END IF;
 PERFORM 1 FROM ativos_ativo WHERE id=NEW.ativo_id FOR UPDATE;
 IF TG_OP='UPDATE' AND (OLD.fim IS NOT NULL OR
    (to_jsonb(NEW)-ARRAY['fim','processo_fim_id']) IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['fim','processo_fim_id'])) THEN
  RAISE EXCEPTION 'Responsabilidade imutavel' USING ERRCODE='23514';
 END IF;
 IF TG_OP='INSERT' AND NOT EXISTS(SELECT 1 FROM termos_termo WHERE processo_id=NEW.processo_inicio_id AND estado='ASSINADO') THEN
  RAISE EXCEPTION 'Entrega assinada obrigatoria' USING ERRCODE='23514';
 END IF;
 IF NEW.fim IS NOT NULL AND NOT EXISTS(SELECT 1 FROM termos_termo WHERE processo_id=NEW.processo_fim_id AND estado='ASSINADO') THEN
  RAISE EXCEPTION 'Devolucao assinada obrigatoria' USING ERRCODE='23514';
 END IF;
 SELECT c.multiplos_responsaveis INTO multi FROM ativos_ativo a JOIN cadastros_categoriaativo c ON c.id=a.categoria_id WHERE a.id=NEW.ativo_id;
 IF NEW.fim IS NULL AND NOT multi AND EXISTS(SELECT 1 FROM movimentacoes_responsabilidadeativo WHERE ativo_id=NEW.ativo_id AND fim IS NULL AND id<>NEW.id) THEN
  RAISE EXCEPTION 'Responsabilidade simultanea incompativel' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER responsabilidade_protegida BEFORE INSERT OR UPDATE OR DELETE ON movimentacoes_responsabilidadeativo
FOR EACH ROW EXECUTE FUNCTION gati_responsibility_guard();

CREATE FUNCTION gati_file_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Arquivo historico' USING ERRCODE='23514'; END IF;
 IF (to_jsonb(NEW)-ARRAY['ativo','versao','atualizado_em']) IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['ativo','versao','atualizado_em']) THEN
  RAISE EXCEPTION 'Metadados do arquivo imutaveis' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER arquivo_protegido BEFORE UPDATE OR DELETE ON arquivos_arquivo
FOR EACH ROW EXECUTE FUNCTION gati_file_guard();
"""

REVERSE = """
DROP FUNCTION gati_append_only() CASCADE;
DROP FUNCTION gati_term_guard() CASCADE;
DROP FUNCTION gati_item_guard() CASCADE;
DROP FUNCTION gati_signature_guard() CASCADE;
DROP FUNCTION gati_process_item_guard() CASCADE;
DROP FUNCTION gati_process_guard() CASCADE;
DROP FUNCTION gati_responsibility_guard() CASCADE;
DROP FUNCTION gati_file_guard() CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("termos", "0001_initial"),
        ("movimentacoes", "0002_initial"),
        ("auditoria", "0002_initial"),
        ("arquivos", "0002_initial"),
    ]
    operations = [migrations.RunSQL(SQL, REVERSE)]
