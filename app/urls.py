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

    path("pedidos/", views.PedidoListView.as_view(), name="pedido_lista"),
    path("pedidos/novo/", views.PedidoCreateView.as_view(), name="pedido_novo"),
    path("pedidos/<int:pk>/", views.PedidoDetailView.as_view(), name="pedido_detalhe"),
    path("pedidos/<int:pk>/editar/", views.PedidoUpdateView.as_view(), name="pedido_editar"),
    path("pedidos/<int:pk>/aprovar/", views.pedido_aprovar, name="pedido_aprovar"),
    path("pedidos/<int:pk>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),
    path("pedidos/<int:pk>/faturar/", views.pedido_faturar, name="pedido_faturar"),
    path("vendas/", views.VendaListView.as_view(), name="venda_lista"),
    path("vendas/<int:pk>/", views.VendaDetailView.as_view(), name="venda_detalhe"),
    path("vendas/<int:pk>/pagamento/", views.venda_pagamento, name="venda_pagamento"),
    path("vendas/<int:pk>/devolucao/", views.venda_devolucao, name="venda_devolucao"),
    path("vendas/<int:pk>/cancelar/", views.venda_cancelar, name="venda_cancelar"),
    path("compras/", views.CompraListView.as_view(), name="compra_lista"),
    path("compras/nova/", views.CompraCreateView.as_view(), name="compra_novo"),
    path("compras/<int:pk>/", views.CompraDetailView.as_view(), name="compra_detalhe"),
    path("compras/<int:pk>/editar/", views.CompraUpdateView.as_view(), name="compra_editar"),
    path("compras/<int:pk>/receber/", views.compra_receber, name="compra_receber"),
    path("compras/<int:pk>/cancelar/", views.compra_cancelar, name="compra_cancelar"),
    
    path("despesas/", views.DespesaListView.as_view(), name="despesa_lista"),
    path("despesas/nova/", views.DespesaCreateView.as_view(), name="despesa_novo"),
    path("despesas/<int:pk>/editar/", views.DespesaUpdateView.as_view(), name="despesa_editar"),
    path("despesas/<int:pk>/excluir/", views.DespesaDeleteView.as_view(), name="despesa_excluir"),
    path("despesas/<int:pk>/pagar/", views.despesa_pagar, name="despesa_pagar"),

    path("comissoes/", views.ComissaoListView.as_view(), name="comissao_lista"),
    path("comissoes/nova/", views.ComissaoCreateView.as_view(), name="comissao_novo"),

    path("promocoes/", views.PromocaoListView.as_view(), name="promocao_lista"),
    path("promocoes/nova/", views.PromocaoCreateView.as_view(), name="promocao_novo"),
    path("promocoes/<int:pk>/editar/", views.PromocaoUpdateView.as_view(), name="promocao_editar"),
    path("promocoes/<int:pk>/excluir/", views.PromocaoDeleteView.as_view(), name="promocao_excluir"),

    path("entregas/", views.EntregaListView.as_view(), name="entrega_lista"),
    path("entregas/nova/", views.EntregaCreateView.as_view(), name="entrega_novo"),
    path("entregas/<int:pk>/editar/", views.EntregaUpdateView.as_view(), name="entrega_editar"),
    path("entregas/<int:pk>/excluir/", views.EntregaDeleteView.as_view(), name="entrega_excluir"),
    path("entregas/<int:pk>/status/", views.entrega_status, name="entrega_status"),
    
    path("relatorios/", views.relatorios_indice, name="relatorio_indice"),
    path("relatorios/<slug:tipo>/", views.relatorio, name="relatorio"),
    path("pedidos/<int:pk>/pdf/", views.pedido_pdf, name="pedido_pdf"),
    path("vendas/<int:pk>/nota/", views.venda_nota, name="venda_nota"),
    path("parcelas/<int:pk>/pagar/", views.parcela_pagar, name="parcela_pagar"),

]

