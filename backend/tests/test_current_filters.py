from datetime import date

from conftest import process_for, sign_all

from gati.apps.ativos.models import Ativo
from gati.apps.movimentacoes.services import create_process
from gati.common.selectors import records


def test_responsibility_search_uses_current_person(domain):
    d = domain
    sign_all(d, process_for(d))
    sign_all(d, process_for(d, kind="DEVOLUCAO"))
    process = create_process(
        d.operator,
        {
            "tipo": "ENTREGA",
            "responsavel": d.witness,
            "localizacao": d.destination,
            "data": date.today(),
        },
        [{"ativo": d.asset, "condicoes": "Conferido"}],
        d.template,
        [{"pessoa": d.witness, "papel": "RESPONSAVEL", "metodo": "PRESENCIAL"}],
    )
    sign_all(d, process)
    assert not records("ativos", Ativo, {"responsavel": str(d.person.pk)}).exists()
    assert records("ativos", Ativo, {"responsavel": str(d.witness.pk)}).count() == 1
