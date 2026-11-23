from django import forms
from django.forms import inlineformset_factory

from .models import Devolucao, ItemPedido, Pagamento, Pedido, Produto


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