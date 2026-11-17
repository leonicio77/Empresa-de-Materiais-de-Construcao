from django.contrib import admin
from .models import Cliente, Fornecedor, Funcionario, Categoria, Produto

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf_cnpj", "telefone", "email")
    search_fields = ("nome","cpf_cnpj")

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf_cnpj", "telefone", "email")
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
    list_display = ("nome", "categoria", "qtd_estoque", "estoque_minimo", "preco_unidade")
    list_filter = ("categoria", "fornecedor")
    search_fields = ("nome",)     



