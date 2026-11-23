from django import forms
from django.forms import inlineformset_factory

from .models import ItemPedido, Pedido


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