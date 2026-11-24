from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

# Quais cargos acessam cada área. O administrador acessa tudo.
PERMISSOES = {
    "clientes": {"gerente", "vendedor", "caixa"},
    "fornecedores": {"gerente", "estoquista"},
    "funcionarios": set(),
    "produtos": {"gerente", "estoquista"},
    "estoque": {"gerente", "estoquista"},
    "pedidos": {"gerente", "vendedor", "caixa"},
    "vendas": {"gerente", "vendedor", "caixa"},
    "compras": {"gerente", "estoquista"},
    "entregas": {"gerente", "caixa", "entregador"},
    "despesas": {"gerente", "caixa"},
    "comissoes": {"gerente"},
    "promocoes": {"gerente"},
    "relatorios": {"gerente"},
}

# Para as views genéricas descobrirem a área pelo model.
AREA_POR_MODEL = {
    "Cliente": "clientes",
    "Fornecedor": "fornecedores",
    "Funcionario": "funcionarios",
    "Categoria": "produtos",
    "Produto": "produtos",
    "MovimentacaoEstoque": "estoque",
    "Pedido": "pedidos",
    "Venda": "vendas",
    "Compra": "compras",
    "Despesa": "despesas",
    "Comissao": "comissoes",
    "Promocao": "promocoes",
    "Entrega": "entregas",
}


def areas_do_usuario(user):
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set(PERMISSOES)
    funcionario = getattr(user, "funcionario", None)
    if funcionario is None:
        return set()
    if funcionario.cargo == "admin":
        return set(PERMISSOES)
    return {
        area for area, cargos in PERMISSOES.items()
        if funcionario.cargo in cargos
    }


def pode_acessar(user, area):
    return area in areas_do_usuario(user)


class AreaMixin(LoginRequiredMixin):
    area = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            area = self.area or AREA_POR_MODEL.get(self.model.__name__)
            if not pode_acessar(request.user, area):
                messages.error(
                    request, "Você não tem permissão para acessar esta área."
                )
                return redirect("home")
        return super().dispatch(request, *args, **kwargs)


def area_required(area):
    def decorador(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not pode_acessar(request.user, area):
                messages.error(
                    request, "Você não tem permissão para realizar esta ação."
                )
                return redirect("home")
            return view(request, *args, **kwargs)
        return wrapper
    return decorador