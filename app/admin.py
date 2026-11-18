from django.contrib import admin
from .models import (
    Cliente, Fornecedor, Funcionario, Categoria, Produto,
    Promocao, MovimentacaoEstoque, Pedido, ItemPedido
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf_cnpj", "telefone")
    search_fields = ("nome", "cpf_cnpj")


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf_cnpj", "telefone")
    search_fields = ("nome", "cpf_cnpj")


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "cargo", "telefone")
    list_filter = ("cargo",)
    search_fields = ("nome", "cpf")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ("nome",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome", "categoria", "qtd_estoque", "estoque_minimo",
        "preco_unidade", "abaixo_do_minimo",
    )
    list_filter = ("categoria", "fornecedor")
    search_fields = ("nome",)


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "desconto", "data_inicio", "data_fim")
    filter_horizontal = ("produtos",)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "tipo", "quantidade", "data")
    list_filter = ("tipo",)

    def has_change_permission(self, request, obj=None):
        return obj is None


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    readonly_fields = ("subtotal",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "vendedor", 
    "data", "status", "valor_total"
    )  
    list_filter = ("status",)   
    search_fields  = ("cliente__nome",)
    inlines = [ItemPedidoInline]
    readonly_fields = ("subtotal", "valor_total")
