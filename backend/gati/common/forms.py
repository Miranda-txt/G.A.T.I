from django import forms
from django.db import models

from .registry import RESOURCES


class StyledForm:
    def style(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else ("form-select" if isinstance(field.widget, forms.Select) else "form-control")
            )
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 5


def record_form(resource, data=None, instance=None):
    config = RESOURCES[resource]
    fields = list(config.fields)
    widgets = {}
    for field in config.model._meta.fields:
        if isinstance(field, models.DateField):
            widgets[field.name] = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    Form = forms.modelform_factory(config.model, fields=fields, widgets=widgets)
    form = Form(data=data, instance=instance)
    for name, field in form.fields.items():
        if isinstance(field, forms.ModelChoiceField):
            field.queryset = field.queryset.filter(ativo=True)
        if isinstance(field, forms.DateField):
            field.input_formats = ["%Y-%m-%d"]
        field.widget.attrs["class"] = (
            "form-check-input"
            if isinstance(field.widget, forms.CheckboxInput)
            else ("form-select" if isinstance(field.widget, forms.Select) else "form-control")
        )
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs["rows"] = 6
    form.fields["versao"] = forms.IntegerField(
        widget=forms.HiddenInput, initial=instance.versao if instance else 1
    )
    return form
