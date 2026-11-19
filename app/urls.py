from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("clientes/", views.ClienteListView.as_view(), name="cliente_lista"),
    path("clientes/novo/", views.ClienteCreateView.as_view(), name="cliente_novo"),
    path("clientes/<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente_editar"),
    path("clientes/<int:pk>/excluir/", views.ClienteDeleteView.as_view(), name="cliente_excluir"),
    path("fornecedores/", views.FornecedorListView.as_view(), name="fornecedor_lista"),
    path("fornecedores/novo/", views.FornecedorCreateView.as_view(), name="fornecedor_novo"),
    path("fornecedores/<int:pk>/editar/", views.FornecedorUpdateView.as_view(), name="fornecedor_editar"),
    path("fornecedores/<int:pk>/excluir/", views.FornecedorDeleteView.as_view(), name="fornecedor_excluir"),
    path("funcionarios/", views.FuncionarioListView.as_view(), name="funcionario_lista"),
    path("funcionarios/novo/", views.FuncionarioCreateView.as_view(), name="funcionario_novo"),
    path("funcionarios/<int:pk>/editar/", views.FuncionarioUpdateView.as_view(), name="funcionario_editar"),
    path("funcionarios/<int:pk>/excluir/", views.FuncionarioDeleteView.as_view(), name="funcionario_excluir"),

    path("categorias/", views.CategoriaListView.as_view(), name="categoria_lista"),
    path("categorias/nova/", views.CategoriaCreateView.as_view(), name="categoria_novo"),
    path("categorias/<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="categoria_editar"),
    path("categorias/<int:pk>/excluir/", views.CategoriaDeleteView.as_view(), name="categoria_excluir"),

    path("produtos/", views.ProdutoListView.as_view(), name="produto_lista"),
    path("produtos/novo/", views.ProdutoCreateView.as_view(), name="produto_novo"),
    path("produtos/<int:pk>/editar/", views.ProdutoUpdateView.as_view(), name="produto_editar"),
    path("produtos/<int:pk>/excluir/", views.ProdutoDeleteView.as_view(), name="produto_excluir"),

    path("estoque/", views.MovimentacaoListView.as_view(), name="movimentacao_lista"),
    path("estoque/nova/", views.MovimentacaoCreateView.as_view(), name="movimentacao_novo"),
]

