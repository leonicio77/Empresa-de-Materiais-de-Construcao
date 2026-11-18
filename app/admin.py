from django.contrib import admin
from django.utils import timezone
from .models import (
    Cliente, Fornecedor, Funcionario, Categoria, Produto,
    Promocao, MovimentacaoEstoque, Pedido, ItemPedido, Venda, Compra,
    ItemCompra, Despesa, Comissao,
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

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "cliente", "vendedor", "data",
                    "forma_pagamento", "valor_total", "status")
    list_filter = ("status", "forma_pagamento")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("pedido", "forma_pagamento")
        return ()

class ItemCompraInline(admin.TabularInline):
    model = ItemCompra
    extra = 1

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("id", "fornecedor", "data", "status", "valor_total")
    list_filter = ("status", "fornecedor")
    inlines = [ItemCompraInline]
    readonly_fields = ("status", "valor_total")
    actions = ["marcar_como_recebida", "cancelar_compra"]

    @admin.action(description="Marcar compras selecionadas como recebidas")
    def marcar_como_recebida(self, request, queryset):
        recebidas = 0
        for compra in queryset.filter(status="pendente"):
            compra.receber()
            recebidas += 1
        self.message_user(request, f"{recebidas} compra(s) recebida(s). Estoque atualizado.")

    @admin.action(description="Cancelar compras selecionadas")
    def cancelar_compra(self, request, queryset):
        canceladas = 0
        for compra in queryset.filter(status="pendente"):
            compra.cancelar()
            canceladas += 1
        self.message_user(request, f"{canceladas} compra(s) cancelada(s).") 

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "descricao", "valor", "vencimento", "data_pagamento", "status")
    list_filter = ("tipo",)
    search_fields = ("descricao",)
    actions = ["marcar_como_paga"]

    @admin.action(description="Marcar despesas selecionadas como pagas (hoje)")
    def marcar_como_paga(self, request, queryset):
        atualizadas = queryset.filter(data_pagamento__isnull=True).update(
            data_pagamento=timezone.localdate()
        )
        self.message_user(request, f"{atualizadas} despesa(s) marcada(s) como paga(s).")


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ("vendedor", "data_inicio", "data_fim",
                    "valor_vendas", "percentual", "valor_comissao")
    list_filter = ("vendedor",)

    def get_readonly_fields(self, request, obj=None):
        calculados = ("valor_vendas", "percentual", "valor_comissao", "despesa")
        if obj:
            return calculados + ("vendedor", "data_inicio", "data_fim")
        return calculados            