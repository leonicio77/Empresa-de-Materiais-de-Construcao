from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import ItemPedidoFormSet
from .models import (
    Categoria, Cliente, Fornecedor, Funcionario, MovimentacaoEstoque,
    Pedido, Produto, Venda,
)

@login_required
def home(request):
    return render(request, "home.html")


# ---------- Views-base (a lógica comum a todos os cadastros) ----------

class BaseListView(LoginRequiredMixin, ListView):
    campos_busca = ()
    ordenacao = "nome"

    def get_queryset(self):
        objetos = super().get_queryset().order_by(self.ordenacao)
        busca = self.request.GET.get("q", "").strip()
        if busca and self.campos_busca:
            filtro = Q()
            for campo in self.campos_busca:
                filtro |= Q(**{f"{campo}__icontains": busca})
            objetos = objetos.filter(filtro)
        return objetos

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["busca"] = self.request.GET.get("q", "")
        return contexto


class BaseFormMixin(LoginRequiredMixin, SuccessMessageMixin):
    template_name = "crud/form.html"
    prefixo = ""
    nome = ""

    def get_success_url(self):
        return reverse(f"{self.prefixo}_lista")

    def get_success_message(self, cleaned_data):
        return "Cadastro salvo com sucesso."

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["nome"] = self.nome
        contexto["url_lista"] = f"{self.prefixo}_lista"
        return contexto


class BaseCreateView(BaseFormMixin, CreateView):
    pass


class BaseUpdateView(BaseFormMixin, UpdateView):
    pass


class BaseDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "crud/confirmar_exclusao.html"
    prefixo = ""
    nome = ""

    def get_success_url(self):
        return reverse(f"{self.prefixo}_lista")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["nome"] = self.nome
        contexto["url_lista"] = f"{self.prefixo}_lista"
        return contexto

    def form_valid(self, form):
        try:
            resposta = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"Não é possível excluir: este {self.nome} está sendo usado "
                "em outros registros.",
            )
            return redirect(f"{self.prefixo}_lista")
        messages.success(self.request, "Cadastro excluído com sucesso.")
        return resposta


# ---------- Clientes ----------

class ClienteListView(BaseListView):
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    campos_busca = ("nome", "cpf_cnpj")


class ClienteCreateView(BaseCreateView):
    model = Cliente
    fields = ["nome", "cpf_cnpj", "telefone", "endereco", "email"]
    prefixo = "cliente"
    nome = "cliente"


class ClienteUpdateView(BaseUpdateView):
    model = Cliente
    fields = ["nome", "cpf_cnpj", "telefone", "endereco", "email"]
    prefixo = "cliente"
    nome = "cliente"


class ClienteDeleteView(BaseDeleteView):
    model = Cliente
    prefixo = "cliente"
    nome = "cliente"


# ---------- Fornecedores ----------

class FornecedorListView(BaseListView):
    model = Fornecedor
    template_name = "fornecedores/lista.html"
    context_object_name = "fornecedores"
    campos_busca = ("nome", "cpf_cnpj")


class FornecedorCreateView(BaseCreateView):
    model = Fornecedor
    fields = ["nome", "cpf_cnpj", "endereco", "telefone", "email"]
    prefixo = "fornecedor"
    nome = "fornecedor"


class FornecedorUpdateView(BaseUpdateView):
    model = Fornecedor
    fields = ["nome", "cpf_cnpj", "endereco", "telefone", "email"]
    prefixo = "fornecedor"
    nome = "fornecedor"


class FornecedorDeleteView(BaseDeleteView):
    model = Fornecedor
    prefixo = "fornecedor"
    nome = "fornecedor"

# ---------- Funcionários ----------

class FuncionarioListView(BaseListView):
    model = Funcionario
    template_name = "funcionarios/lista.html"
    context_object_name = "funcionarios"
    campos_busca = ("nome", "cpf", "cargo")


class FuncionarioCreateView(BaseCreateView):
    model = Funcionario
    fields = ["nome", "cpf", "telefone", "endereco", "cargo",
              "salario", "percentual_comissao"]
    prefixo = "funcionario"
    nome = "funcionário"


class FuncionarioUpdateView(BaseUpdateView):
    model = Funcionario
    fields = ["nome", "cpf", "telefone", "endereco", "cargo",
              "salario", "percentual_comissao"]
    prefixo = "funcionario"
    nome = "funcionário"


class FuncionarioDeleteView(BaseDeleteView):
    model = Funcionario
    prefixo = "funcionario"
    nome = "funcionário"


# ---------- Categorias ----------

class CategoriaListView(BaseListView):
    model = Categoria
    template_name = "categorias/lista.html"
    context_object_name = "categorias"
    campos_busca = ("nome",)


class CategoriaCreateView(BaseCreateView):
    model = Categoria
    fields = ["nome"]
    prefixo = "categoria"
    nome = "categoria"


class CategoriaUpdateView(BaseUpdateView):
    model = Categoria
    fields = ["nome"]
    prefixo = "categoria"
    nome = "categoria"


class CategoriaDeleteView(BaseDeleteView):
    model = Categoria
    prefixo = "categoria"
    nome = "categoria"


# ---------- Produtos ----------

class ProdutoListView(BaseListView):
    model = Produto
    template_name = "produtos/lista.html"
    context_object_name = "produtos"
    campos_busca = ("nome", "categoria__nome", "fornecedor__nome")

    def get_queryset(self):
        return super().get_queryset().select_related("categoria", "fornecedor")


class ProdutoCreateView(BaseCreateView):
    model = Produto
    fields = ["nome", "descricao", "categoria", "fornecedor",
              "estoque_minimo", "m2", "preco_unidade"]
    prefixo = "produto"
    nome = "produto"


class ProdutoUpdateView(BaseUpdateView):
    model = Produto
    fields = ["nome", "descricao", "categoria", "fornecedor",
              "estoque_minimo", "m2", "preco_unidade"]
    prefixo = "produto"
    nome = "produto"


class ProdutoDeleteView(BaseDeleteView):
    model = Produto
    prefixo = "produto"
    nome = "produto"    

# ---------- Estoque (movimentações) ----------

class MovimentacaoListView(BaseListView):
    model = MovimentacaoEstoque
    template_name = "estoque/lista.html"
    context_object_name = "movimentacoes"
    campos_busca = ("produto__nome", "observacao")
    ordenacao = "-data"
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related("produto")


class MovimentacaoCreateView(BaseCreateView):
    model = MovimentacaoEstoque
    fields = ["produto", "tipo", "quantidade", "observacao"]
    prefixo = "movimentacao"
    nome = "movimentação de estoque" 

# ---------- Pedidos ----------

class PedidoListView(BaseListView):
    model = Pedido
    template_name = "pedidos/lista.html"
    context_object_name = "pedidos"
    campos_busca = ("cliente__nome",)
    ordenacao = "-data"
    paginate_by = 20

    def get_queryset(self):
        pedidos = (
            super().get_queryset()
            .select_related("cliente", "vendedor")
            .prefetch_related("itens")
        )
        status = self.request.GET.get("status", "")
        if status:
            pedidos = pedidos.filter(status=status)
        return pedidos

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["status_atual"] = self.request.GET.get("status", "")
        contexto["opcoes_status"] = Pedido.STATUS
        return contexto


class PedidoSalvarMixin(LoginRequiredMixin):
    model = Pedido
    fields = ["cliente", "vendedor", "desconto"]
    template_name = "pedidos/form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            contexto["formset"] = ItemPedidoFormSet(
                self.request.POST, instance=self.object
            )
        else:
            contexto["formset"] = ItemPedidoFormSet(instance=self.object)
        return contexto

    def form_valid(self, form):
        formset = ItemPedidoFormSet(self.request.POST, instance=self.object)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, "Pedido salvo com sucesso.")
        return redirect("pedido_detalhe", pk=self.object.pk)


class PedidoCreateView(PedidoSalvarMixin, CreateView):
    pass


class PedidoUpdateView(PedidoSalvarMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            pedido = self.get_object()
            if pedido.status != "aberto":
                messages.error(request, "Só é possível editar pedidos abertos.")
                return redirect("pedido_detalhe", pk=pedido.pk)
        return super().dispatch(request, *args, **kwargs)


class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = "pedidos/detalhe.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["itens"] = self.object.itens.select_related("produto")
        contexto["formas_pagamento"] = Venda.FORMAS_PAGAMENTO
        return contexto


@login_required
@require_POST
def pedido_aprovar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if pedido.status != "aberto":
        messages.error(request, "Só pedidos abertos podem ser aprovados.")
    elif not pedido.itens.exists():
        messages.error(request, "O pedido não tem itens.")
    else:
        pedido.status = "aprovado"
        pedido.save()
        messages.success(request, "Pedido aprovado.")
    return redirect("pedido_detalhe", pk=pk)


@login_required
@require_POST
def pedido_cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if pedido.status not in ("aberto", "aprovado"):
        messages.error(request, "Este pedido não pode ser cancelado aqui.")
    else:
        pedido.status = "cancelado"
        pedido.save()
        messages.success(request, "Pedido cancelado.")
    return redirect("pedido_detalhe", pk=pk)


@login_required
@require_POST
def pedido_faturar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    venda = Venda(
        pedido=pedido,
        forma_pagamento=request.POST.get("forma_pagamento", ""),
    )
    try:
        venda.full_clean()
        venda.save()
    except ValidationError as erro:
        for mensagem in erro.messages:
            messages.error(request, mensagem)
    else:
        messages.success(request, "Venda registrada e estoque atualizado.")
    return redirect("pedido_detalhe", pk=pk)       