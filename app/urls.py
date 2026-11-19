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
]

