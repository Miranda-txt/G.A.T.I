"""Contratos renderizados dos componentes compartilhados (DU-UX-DASH-05.2)."""

import re

import pytest
from django import forms
from django.template.loader import render_to_string


def test_field_help_and_errors_resolve_describedby():
    form = forms.Form(data={"contact": "invalido"})
    form.fields["contact"] = forms.EmailField(label="E-mail", help_text="Informe seu e-mail.")
    assert not form.is_valid()
    html = render_to_string("components/form.html", {"form": form})
    field = re.search(r'<input\b[^>]*name="contact"[^>]*>', html)[0]
    assert 'aria-invalid="true"' in field
    describedby = re.search(r'aria-describedby="([^"]+)"', field)[1].split()
    assert set(describedby) == {"id_contact_helptext", "id_contact_error"}
    for element_id in describedby:
        assert html.count(f'id="{element_id}"') == 1, element_id
    assert 'for="id_contact"' in html


@pytest.mark.parametrize(("resource", "columns"), [("ativos", 6), ("pessoas", 5), ("departamentos", 3)])
def test_empty_record_row_spans_actual_columns(domain, client, resource, columns):
    client.force_login(domain.admin)
    response = client.get(f"/cadastros/{resource}/?q=SEM-REGISTROS-TESTE-05", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    html = response.content.decode()
    assert html.count('scope="col"') == columns
    assert re.search(rf'<td colspan="{columns}">\s*<div class="empty-state">', html)


def test_wizard_exposes_exactly_one_current_step(domain, client):
    client.force_login(domain.operator)
    response = client.get("/processos/novo/1/")
    assert response.status_code == 200
    html = response.content.decode()
    assert html.count('aria-current="step"') == 1
    assert re.search(r'<li\b[^>]*aria-current="step"[^>]*>\s*<span>1</span>', html)
