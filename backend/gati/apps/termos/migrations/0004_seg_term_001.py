"""SEG-TERM-001: enforce valid term state transitions and nonempty signed set.

This migration is deliberately irreversible: rolling back to the prior function
would reintroduce a confirmed integrity defect. Plan recovery before applying.
"""

from django.db import migrations

SQL = r"""
CREATE OR REPLACE FUNCTION public.gati_term_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Termo nao pode ser excluido' USING ERRCODE = '23514';
    END IF;

    IF TG_OP = 'INSERT' THEN
        IF NEW.estado <> 'EM_EDICAO' THEN
            RAISE EXCEPTION 'Estado inicial invalido' USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END IF;

    -- Never modify the frozen document after it has been issued.
    IF OLD.estado <> 'EM_EDICAO' THEN
        IF (to_jsonb(NEW) - ARRAY[
                'estado', 'versao', 'atualizado_em', 'cancelado_em', 'motivo_cancelamento'
            ]) IS DISTINCT FROM
           (to_jsonb(OLD) - ARRAY[
                'estado', 'versao', 'atualizado_em', 'cancelado_em', 'motivo_cancelamento'
            ]) THEN
            RAISE EXCEPTION 'Conteudo congelado' USING ERRCODE = '23514';
        END IF;
        IF OLD.estado = 'CANCELADO' AND to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
            RAISE EXCEPTION 'Cancelamento imutavel' USING ERRCODE = '23514';
        END IF;
    END IF;

    -- Check EVERY transition, including transitions starting in EM_EDICAO.
    IF NEW.estado IS DISTINCT FROM OLD.estado AND NOT (
         (OLD.estado = 'EM_EDICAO' AND NEW.estado IN ('AGUARDANDO_ASSINATURAS', 'CANCELADO'))
      OR (OLD.estado = 'AGUARDANDO_ASSINATURAS' AND NEW.estado IN ('ASSINADO', 'CANCELADO'))
      OR (OLD.estado = 'ASSINADO' AND NEW.estado = 'CANCELADO')
    ) THEN
        RAISE EXCEPTION 'Transicao invalida' USING ERRCODE = '23514';
    END IF;

    -- A document must have at least one signer when entering the signing phase.
    IF NEW.estado = 'AGUARDANDO_ASSINATURAS' AND NOT EXISTS (
        SELECT 1 FROM public.termos_assinaturatermo WHERE termo_id = NEW.id
    ) THEN
        RAISE EXCEPTION 'Signatario obrigatorio' USING ERRCODE = '23514';
    END IF;

    -- An empty set of signatures must NOT count as all signatures completed.
    IF NEW.estado = 'ASSINADO' AND (
        NOT EXISTS (
            SELECT 1 FROM public.termos_assinaturatermo WHERE termo_id = NEW.id
        )
        OR EXISTS (
            SELECT 1 FROM public.termos_assinaturatermo
            WHERE termo_id = NEW.id
              AND (assinado_em IS NULL OR hash_assinado IS DISTINCT FROM NEW.sha256)
        )
    ) THEN
        RAISE EXCEPTION 'Faltam assinaturas validas' USING ERRCODE = '23514';
    END IF;

    IF NEW.estado = 'CANCELADO'
       AND (NEW.cancelado_em IS NULL OR length(btrim(NEW.motivo_cancelamento)) < 10) THEN
        RAISE EXCEPTION 'Cancelamento exige motivo' USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END $$;

-- The original trigger did not inspect INSERT; restrict direct pre-signed inserts too.
DROP TRIGGER IF EXISTS termo_congelado ON public.termos_termo;
CREATE TRIGGER termo_congelado
BEFORE INSERT OR UPDATE OR DELETE ON public.termos_termo
FOR EACH ROW EXECUTE FUNCTION public.gati_term_guard();
"""


class Migration(migrations.Migration):
    atomic = True
    dependencies = [("termos", "0003_termo_substitui")]
    operations = [migrations.RunSQL(SQL)]
