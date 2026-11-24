from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from .models import (
    Comissao, Compra, Despesa, Entrega, ItemPedido, Produto, Venda,
)


def moeda(valor):
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(valor):
    return valor.strftime("%d/%m/%Y") if valor else "-"


def ler_data(texto, padrao):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return padrao


def vendas(inicio, fim, vendedor):
    consulta = (
        Venda.objects.filter(
            status="concluida", data__date__gte=inicio, data__date__lte=fim
        )
        .select_related("pedido__cliente", "pedido__vendedor")
        .prefetch_related("pedido__itens", "devolucoes")
        .order_by("data")
    )
    if vendedor:
        consulta = consulta.filter(pedido__vendedor_id=vendedor)
    linhas, total = [], Decimal("0")
    for v in consulta:
        total += v.valor_total
        linhas.append([
            v.pk,
            timezone.localtime(v.data).strftime("%d/%m/%Y %H:%M"),
            str(v.cliente),
            str(v.vendedor),
            v.get_forma_pagamento_display(),
            moeda(v.valor_total),
        ])
    resumo = [("Vendas", len(linhas)), ("Total vendido", "R$ " + moeda(total))]
    if linhas:
        resumo.append(("Ticket médio", "R$ " + moeda(total / len(linhas))))
    return {
        "colunas": ["Nº", "Data", "Cliente", "Vendedor", "Pagamento", "Valor (R$)"],
        "linhas": linhas,
        "resumo": resumo,
    }


def mais_vendidos(inicio, fim, vendedor):
    consulta = ItemPedido.objects.filter(
        pedido__venda__status="concluida",
        pedido__venda__data__date__gte=inicio,
        pedido__venda__data__date__lte=fim,
    )
    if vendedor:
        consulta = consulta.filter(pedido__vendedor_id=vendedor)
    receita = ExpressionWrapper(
        F("quantidade") * F("preco_unitario"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    itens = (
        consulta.values("produto__nome")
        .annotate(qtd=Sum("quantidade"), valor=Sum(receita))
        .order_by("-qtd")[:20]
    )
    linhas = [[i["produto__nome"], i["qtd"], moeda(i["valor"])] for i in itens]
    return {
        "colunas": ["Produto", "Quantidade vendida", "Receita (R$)"],
        "linhas": linhas,
        "resumo": [("Produtos listados", len(linhas))],
    }


def estoque(inicio, fim, vendedor):
    produtos = Produto.objects.select_related("categoria", "fornecedor").order_by("nome")
    linhas, valor, baixos = [], Decimal("0"), 0
    for p in produtos:
        valor += p.qtd_estoque * p.preco_unidade
        if p.abaixo_do_minimo:
            baixos += 1
        linhas.append([
            p.nome,
            str(p.categoria),
            str(p.fornecedor),
            p.qtd_estoque,
            p.estoque_minimo,
            "Baixo" if p.abaixo_do_minimo else "OK",
        ])
    return {
        "colunas": ["Produto", "Categoria", "Fornecedor", "Estoque", "Mínimo", "Situação"],
        "linhas": linhas,
        "resumo": [
            ("Produtos", len(linhas)),
            ("Abaixo do mínimo", baixos),
            ("Valor em estoque (preço de venda)", "R$ " + moeda(valor)),
        ],
    }


def compras(inicio, fim, vendedor):
    consulta = (
        Compra.objects.filter(
            status="recebida", data__date__gte=inicio, data__date__lte=fim
        )
        .select_related("fornecedor")
        .prefetch_related("itens")
        .order_by("data")
    )
    linhas, total = [], Decimal("0")
    for c in consulta:
        total += c.valor_total
        linhas.append([
            c.pk,
            timezone.localtime(c.data).strftime("%d/%m/%Y %H:%M"),
            str(c.fornecedor),
            moeda(c.valor_total),
        ])
    return {
        "colunas": ["Nº", "Data", "Fornecedor", "Total (R$)"],
        "linhas": linhas,
        "resumo": [("Compras recebidas", len(linhas)), ("Total comprado", "R$ " + moeda(total))],
    }


def despesas(inicio, fim, vendedor):
    consulta = Despesa.objects.filter(
        vencimento__gte=inicio, vencimento__lte=fim
    ).order_by("vencimento")
    linhas, total, pago = [], Decimal("0"), Decimal("0")
    for d in consulta:
        total += d.valor
        if d.data_pagamento:
            pago += d.valor
        linhas.append([
            d.get_tipo_display(),
            d.descricao or "-",
            moeda(d.valor),
            formatar_data(d.vencimento),
            formatar_data(d.data_pagamento),
            d.status,
        ])
    return {
        "colunas": ["Tipo", "Descrição", "Valor (R$)", "Vencimento", "Pagamento", "Situação"],
        "linhas": linhas,
        "resumo": [
            ("Total", "R$ " + moeda(total)),
            ("Pago", "R$ " + moeda(pago)),
            ("Em aberto", "R$ " + moeda(total - pago)),
        ],
    }


def comissoes(inicio, fim, vendedor):
    consulta = (
        Comissao.objects.filter(data_inicio__lte=fim, data_fim__gte=inicio)
        .select_related("vendedor", "despesa")
        .order_by("vendedor__nome", "data_inicio")
    )
    linhas, total = [], Decimal("0")
    for c in consulta:
        total += c.valor_comissao
        linhas.append([
            str(c.vendedor),
            f"{formatar_data(c.data_inicio)} a {formatar_data(c.data_fim)}",
            moeda(c.valor_vendas),
            f"{c.percentual}%",
            moeda(c.valor_comissao),
            c.despesa.status,
        ])
    return {
        "colunas": ["Vendedor", "Período", "Total vendido (R$)", "%", "Comissão (R$)", "Pagamento"],
        "linhas": linhas,
        "resumo": [("Comissões", len(linhas)), ("Total em comissões", "R$ " + moeda(total))],
    }


def entregas(inicio, fim, vendedor):
    consulta = (
        Entrega.objects.filter(data_prevista__gte=inicio, data_prevista__lte=fim)
        .select_related("venda__pedido__cliente", "entregador")
        .order_by("data_prevista")
    )
    linhas, por_status = [], {}
    for e in consulta:
        por_status[e.get_status_display()] = por_status.get(e.get_status_display(), 0) + 1
        linhas.append([
            e.venda_id,
            str(e.venda.cliente),
            e.endereco,
            formatar_data(e.data_prevista),
            str(e.entregador) if e.entregador else "-",
            moeda(e.frete),
            e.get_status_display(),
        ])
    resumo = [("Entregas", len(linhas))] + list(por_status.items())
    return {
        "colunas": ["Venda", "Cliente", "Endereço", "Prevista", "Entregador", "Frete (R$)", "Status"],
        "linhas": linhas,
        "resumo": resumo,
    }


RELATORIOS = {
    "vendas": {
        "titulo": "Vendas por período",
        "descricao": "Vendas concluídas, com total e ticket médio. Dá para filtrar por vendedor.",
        "func": vendas, "periodo": True, "vendedor": True,
    },
    "mais-vendidos": {
        "titulo": "Produtos mais vendidos",
        "descricao": "Os 20 produtos com mais unidades vendidas no período.",
        "func": mais_vendidos, "periodo": True, "vendedor": True,
    },
    "estoque": {
        "titulo": "Estoque atual",
        "descricao": "Todos os produtos, com destaque para os abaixo do mínimo.",
        "func": estoque, "periodo": False, "vendedor": False,
    },
    "compras": {
        "titulo": "Compras recebidas",
        "descricao": "Compras que já entraram no estoque, por período.",
        "func": compras, "periodo": True, "vendedor": False,
    },
    "despesas": {
        "titulo": "Despesas",
        "descricao": "Despesas por data de vencimento, com total pago e em aberto.",
        "func": despesas, "periodo": True, "vendedor": False,
    },
    "comissoes": {
        "titulo": "Comissões",
        "descricao": "Comissões calculadas cujo período cruza o intervalo escolhido.",
        "func": comissoes, "periodo": True, "vendedor": False,
    },
    "entregas": {
        "titulo": "Entregas",
        "descricao": "Entregas por data prevista, com a contagem por status.",
        "func": entregas, "periodo": True, "vendedor": False,
    },
}