from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from .models import (
    Comissao, Compra, Despesa, Devolucao, Entrega, ItemCompra, ItemPedido,
    Pagamento, Pedido, Produto, Promocao, Venda,
)
class ItemPedidoForm(forms.ModelForm):
    quantidade = forms.IntegerField(min_value=1)

    class Meta:
        model = ItemPedido
        fields = ["produto", "quantidade"]

    def save(self, commit=True):
        # Se o produto de um item existente mudou, o preço antigo não vale mais:
        # zerando, o save() do model busca o preço do novo produto.
        if self.instance.pk and "produto" in self.changed_data:
            self.instance.preco_unitario = None
        return super().save(commit=commit)


ItemPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemPedido,
    form=ItemPedidoForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["valor", "forma", "data"]
        widgets = {
            "data": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }


class DevolucaoForm(forms.ModelForm):
    class Meta:
        model = Devolucao
        fields = ["produto", "quantidade", "motivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.venda_id:
            self.fields["produto"].queryset = Produto.objects.filter(
                itempedido__pedido=self.instance.venda.pedido
            ).distinct()

class ItemCompraForm(forms.ModelForm):
    quantidade = forms.IntegerField(min_value=1)
    custo = forms.DecimalField(
        label="Custo unitário",
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        model = ItemCompra
        fields = ["produto", "quantidade", "custo"]


ItemCompraFormSet = inlineformset_factory(
    Compra,
    ItemCompra,
    form=ItemCompraForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)            

class DataInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ["tipo", "descricao", "valor", "vencimento", "data_pagamento"]
        widgets = {
            "vencimento": DataInput(),
            "data_pagamento": DataInput(),
        }

    def clean_valor(self):
        valor = self.cleaned_data["valor"]
        if valor <= 0:
            raise forms.ValidationError("O valor precisa ser maior que zero.")
        return valor


class ComissaoForm(forms.ModelForm):
    class Meta:
        model = Comissao
        fields = ["vendedor", "data_inicio", "data_fim"]
        widgets = {
            "data_inicio": DataInput(),
            "data_fim": DataInput(),
        }
        help_texts = {
            "vendedor": "O valor é calculado automaticamente com as vendas "
                        "concluídas do período e gera uma despesa.",
        }


class PromocaoForm(forms.ModelForm):
    desconto = forms.DecimalField(
        label="Desconto (%)",
        min_value=Decimal("0.01"),
        max_value=Decimal("100"),
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        model = Promocao
        fields = ["nome", "produtos", "desconto", "data_inicio", "data_fim"]
        widgets = {
            "produtos": forms.SelectMultiple(attrs={"size": 10}),
            "data_inicio": DataInput(),
            "data_fim": DataInput(),
        }
        help_texts = {"produtos": "Segure Ctrl para escolher mais de um produto."}

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_inicio")
        fim = dados.get("data_fim")
        if inicio and fim and fim < inicio:
            raise forms.ValidationError(
                "A data de fim não pode ser anterior à data de início."
            )
        return dados


class EntregaForm(forms.ModelForm):
    frete = forms.DecimalField(
        min_value=Decimal("0"), max_digits=10, decimal_places=2, initial=0
    )

    class Meta:
        model = Entrega
        fields = ["venda", "endereco", "data_prevista", "frete", "entregador"]
        widgets = {"data_prevista": DataInput()}
        help_texts = {
            "endereco": "Deixe em branco para usar o endereço do cliente.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "venda" in self.fields:
            self.fields["venda"].queryset = Venda.objects.filter(
                status="concluida", entrega__isnull=True
            )


class EntregaEditForm(EntregaForm):
    class Meta(EntregaForm.Meta):
        fields = ["endereco", "data_prevista", "frete", "entregador", "status"]