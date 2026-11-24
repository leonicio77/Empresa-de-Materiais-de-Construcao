import csv
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, ProtectedError, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from . import relatorios
from .forms import (
    ComissaoForm, DespesaForm, DevolucaoForm, EntregaEditForm, EntregaForm,
    ItemCompraFormSet, ItemPedidoFormSet, PagamentoForm, PromocaoForm,
)
from .models import (
    Categoria, Cliente, Comissao, Compra, Despesa, Devolucao, Entrega,
    Fornecedor, Funcionario, MovimentacaoEstoque, Pagamento, Pedido,
    Produto, Promocao, Venda,
)
from .permissoes import AreaMixin, area_required, areas_do_usuario

@login_required
def home(request):
    areas = areas_do_usuario(request.user)
    hoje = timezone.localdate()
    contexto = {"hoje": hoje}

    if "vendas" in areas:
        vendas = (
            Venda.objects.filter(status="concluida", data__date=hoje)
            .select_related("pedido")
            .prefetch_related("pedido__itens", "devolucoes")
        )
        funcionario = getattr(request.user, "funcionario", None)
        if (
            funcionario
            and funcionario.cargo == "vendedor"
            and not request.user.is_superuser
        ):
            vendas = vendas.filter(pedido__vendedor=funcionario)
        vendas = list(vendas)
        contexto["vendas_hoje_qtd"] = len(vendas)
        contexto["vendas_hoje_total"] = sum(
            (v.valor_total for v in vendas), Decimal("0")
        )

    if "estoque" in areas:
        contexto["estoque_critico"] = list(
            Produto.objects.filter(qtd_estoque__lte=F("estoque_minimo"))
            .order_by("qtd_estoque")[:10]
        )

    if "despesas" in areas:
        em_aberto = Despesa.objects.filter(data_pagamento__isnull=True)
        atrasadas = em_aberto.filter(vencimento__lt=hoje)
        contexto["despesas_atrasadas_total"] = (
            atrasadas.aggregate(total=Sum("valor"))["total"] or 0
        )
        contexto["despesas_atrasadas_qtd"] = atrasadas.count()
        contexto["despesas_a_vencer"] = list(
            em_aberto.filter(
                vencimento__gte=hoje,
                vencimento__lte=hoje + timedelta(days=7),
            ).order_by("vencimento")
        )

    if "entregas" in areas:
        contexto["entregas_pendentes"] = list(
            Entrega.objects.filter(status__in=["pendente", "em_rota"])
            .select_related("venda__pedido__cliente", "entregador")
            .order_by("data_prevista")[:10]
        )

    return render(request, "home.html", contexto)


# ---------- Views-base (a lógica comum a todos os cadastros) ----------

class BaseListView(AreaMixin, ListView):
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


class BaseFormMixin(AreaMixin,  SuccessMessageMixin):
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


class BaseDeleteView(AreaMixin, DeleteView):
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
              "salario", "percentual_comissao", "usuario"]
    prefixo = "funcionario"
    nome = "funcionário"


class FuncionarioUpdateView(BaseUpdateView):
    model = Funcionario
    fields = ["nome", "cpf", "telefone", "endereco", "cargo",
              "salario", "percentual_comissao", "usuario"]
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


class PedidoSalvarMixin(AreaMixin):
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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        funcionario = getattr(self.request.user, "funcionario", None)
        if funcionario and funcionario.cargo == "vendedor":
            form.fields["vendedor"].queryset = Funcionario.objects.filter(
                pk=funcionario.pk
            )
            form.fields["vendedor"].empty_label = None
        return form    


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


class PedidoDetailView(AreaMixin, DetailView):
    model = Pedido
    template_name = "pedidos/detalhe.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["itens"] = self.object.itens.select_related("produto")
        contexto["formas_pagamento"] = Venda.FORMAS_PAGAMENTO
        return contexto


@login_required
@require_POST
@area_required("pedidos")
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
        return redirect("venda_detalhe", pk=venda.pk)
    return redirect("pedido_detalhe", pk=pk)

# ---------- Vendas ----------

def _mostrar_erros(request, formulario):
    for campo, erros in formulario.errors.items():
        for erro in erros:
            if campo == "__all__":
                messages.error(request, erro)
            else:
                rotulo = formulario.fields[campo].label or campo
                messages.error(request, f"{rotulo}: {erro}")


class VendaListView(BaseListView):
    model = Venda
    template_name = "vendas/lista.html"
    context_object_name = "vendas"
    campos_busca = ("pedido__cliente__nome",)
    ordenacao = "-data"
    paginate_by = 20

    def get_queryset(self):
        vendas = (
            super().get_queryset()
            .select_related("pedido__cliente", "pedido__vendedor")
            .prefetch_related("pedido__itens", "pagamentos", "devolucoes")
        )
        status = self.request.GET.get("status", "")
        if status:
            vendas = vendas.filter(status=status)
        return vendas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["status_atual"] = self.request.GET.get("status", "")
        contexto["opcoes_status"] = Venda.STATUS
        return contexto


class VendaDetailView(AreaMixin, DetailView):
    model = Venda
    template_name = "vendas/detalhe.html"

    def get_queryset(self):
        return Venda.objects.select_related("pedido__cliente", "pedido__vendedor")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        venda = self.object
        contexto["itens"] = venda.pedido.itens.select_related("produto")
        contexto["pagamentos"] = venda.pagamentos.all()
        contexto["devolucoes"] = venda.devolucoes.select_related("produto")
        contexto["form_pagamento"] = PagamentoForm(instance=Pagamento(venda=venda))
        contexto["form_devolucao"] = DevolucaoForm(instance=Devolucao(venda=venda))
        return contexto


@login_required
@require_POST
def venda_pagamento(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    if venda.status != "concluida":
        messages.error(request, "Só vendas concluídas recebem pagamentos.")
        return redirect("venda_detalhe", pk=pk)
    formulario = PagamentoForm(request.POST, instance=Pagamento(venda=venda))
    if formulario.is_valid():
        formulario.save()
        messages.success(request, "Pagamento registrado.")
    else:
        _mostrar_erros(request, formulario)
    return redirect("venda_detalhe", pk=pk)


@login_required
@require_POST
def venda_devolucao(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    if venda.status != "concluida":
        messages.error(request, "Só vendas concluídas aceitam devoluções.")
        return redirect("venda_detalhe", pk=pk)
    formulario = DevolucaoForm(request.POST, instance=Devolucao(venda=venda))
    if formulario.is_valid():
        formulario.save()
        messages.success(request, "Devolução registrada e estoque atualizado.")
    else:
        _mostrar_erros(request, formulario)
    return redirect("venda_detalhe", pk=pk)


@login_required
@require_POST
def venda_cancelar(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    venda.motivo_cancelamento = request.POST.get("motivo", "").strip()
    try:
        venda.cancelar()
    except ValidationError as erro:
        for mensagem in erro.messages:
            messages.error(request, mensagem)
    else:
        messages.success(request, "Venda cancelada e estoque devolvido.")
    return redirect("venda_detalhe", pk=pk)  

# ---------- Compras ----------

class CompraListView(BaseListView):
    model = Compra
    template_name = "compras/lista.html"
    context_object_name = "compras"
    campos_busca = ("fornecedor__nome",)
    ordenacao = "-data"
    paginate_by = 20

    def get_queryset(self):
        compras = (
            super().get_queryset()
            .select_related("fornecedor")
            .prefetch_related("itens")
        )
        status = self.request.GET.get("status", "")
        if status:
            compras = compras.filter(status=status)
        return compras

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["status_atual"] = self.request.GET.get("status", "")
        contexto["opcoes_status"] = Compra.STATUS
        return contexto


class CompraSalvarMixin(AreaMixin):
    model = Compra
    fields = ["fornecedor"]
    template_name = "compras/form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            contexto["formset"] = ItemCompraFormSet(
                self.request.POST, instance=self.object
            )
        else:
            contexto["formset"] = ItemCompraFormSet(instance=self.object)
        return contexto

    def form_valid(self, form):
        formset = ItemCompraFormSet(self.request.POST, instance=self.object)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, "Compra salva com sucesso.")
        return redirect("compra_detalhe", pk=self.object.pk)


class CompraCreateView(CompraSalvarMixin, CreateView):
    pass


class CompraUpdateView(CompraSalvarMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            compra = self.get_object()
            if compra.status != "pendente":
                messages.error(request, "Só é possível editar compras pendentes.")
                return redirect("compra_detalhe", pk=compra.pk)
        return super().dispatch(request, *args, **kwargs)


class CompraDetailView(AreaMixin, DetailView):
    model = Compra
    template_name = "compras/detalhe.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["itens"] = self.object.itens.select_related("produto")
        return contexto


@login_required
@require_POST
def compra_receber(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    try:
        compra.receber()
    except ValidationError as erro:
        for mensagem in erro.messages:
            messages.error(request, mensagem)
    else:
        messages.success(request, "Compra recebida e estoque atualizado.")
    return redirect("compra_detalhe", pk=pk)


@login_required
@require_POST
def compra_cancelar(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    try:
        compra.cancelar()
    except ValidationError as erro:
        for mensagem in erro.messages:
            messages.error(request, mensagem)
    else:
        messages.success(request, "Compra cancelada.")
    return redirect("compra_detalhe", pk=pk) 

# ---------- Despesas ----------

class DespesaListView(BaseListView):
    model = Despesa
    template_name = "despesas/lista.html"
    context_object_name = "despesas"
    campos_busca = ("descricao",)
    ordenacao = "vencimento"
    paginate_by = 20

    def get_queryset(self):
        despesas = super().get_queryset()
        situacao = self.request.GET.get("situacao", "")
        hoje = timezone.localdate()
        if situacao == "paga":
            despesas = despesas.filter(data_pagamento__isnull=False)
        elif situacao == "atrasada":
            despesas = despesas.filter(
                data_pagamento__isnull=True, vencimento__lt=hoje
            )
        elif situacao == "a_pagar":
            despesas = despesas.filter(
                data_pagamento__isnull=True, vencimento__gte=hoje
            )
        return despesas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["situacao_atual"] = self.request.GET.get("situacao", "")
        contexto["opcoes_situacao"] = [
            ("a_pagar", "A pagar"), ("atrasada", "Atrasada"), ("paga", "Paga"),
        ]
        total = Despesa.objects.filter(data_pagamento__isnull=True).aggregate(
            total=Sum("valor")
        )["total"]
        contexto["total_em_aberto"] = total or 0
        return contexto


class DespesaCreateView(BaseCreateView):
    model = Despesa
    form_class = DespesaForm
    prefixo = "despesa"
    nome = "despesa"


class DespesaUpdateView(BaseUpdateView):
    model = Despesa
    form_class = DespesaForm
    prefixo = "despesa"
    nome = "despesa"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            despesa = self.get_object()
            if Comissao.objects.filter(despesa=despesa).exists():
                messages.error(
                    request,
                    "Despesas geradas por comissão só podem ser marcadas como pagas.",
                )
                return redirect("despesa_lista")
        return super().dispatch(request, *args, **kwargs)


class DespesaDeleteView(BaseDeleteView):
    model = Despesa
    prefixo = "despesa"
    nome = "despesa"


@login_required
@require_POST
def despesa_pagar(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    if despesa.data_pagamento:
        messages.error(request, "Esta despesa já está paga.")
    else:
        despesa.data_pagamento = timezone.localdate()
        despesa.save()
        messages.success(request, "Despesa marcada como paga.")
    return redirect("despesa_lista")


# ---------- Comissões ----------

class ComissaoListView(BaseListView):
    model = Comissao
    template_name = "comissoes/lista.html"
    context_object_name = "comissoes"
    campos_busca = ("vendedor__nome",)
    ordenacao = "-criada_em"
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related("vendedor", "despesa")


class ComissaoCreateView(BaseCreateView):
    model = Comissao
    form_class = ComissaoForm
    prefixo = "comissao"
    nome = "comissão"


# ---------- Promoções ----------

class PromocaoListView(BaseListView):
    model = Promocao
    template_name = "promocoes/lista.html"
    context_object_name = "promocoes"
    campos_busca = ("nome",)
    ordenacao = "-data_inicio"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("produtos")


class PromocaoCreateView(BaseCreateView):
    model = Promocao
    form_class = PromocaoForm
    prefixo = "promocao"
    nome = "promoção"


class PromocaoUpdateView(BaseUpdateView):
    model = Promocao
    form_class = PromocaoForm
    prefixo = "promocao"
    nome = "promoção"


class PromocaoDeleteView(BaseDeleteView):
    model = Promocao
    prefixo = "promocao"
    nome = "promoção"


# ---------- Entregas ----------

class EntregaListView(BaseListView):
    model = Entrega
    template_name = "entregas/lista.html"
    context_object_name = "entregas"
    campos_busca = ("venda__pedido__cliente__nome", "endereco")
    ordenacao = "data_prevista"
    paginate_by = 20

    def get_queryset(self):
        entregas = super().get_queryset().select_related(
            "venda__pedido__cliente", "entregador"
        )
        status = self.request.GET.get("status", "")
        if status:
            entregas = entregas.filter(status=status)
        return entregas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["status_atual"] = self.request.GET.get("status", "")
        contexto["opcoes_status"] = Entrega.STATUS
        return contexto


class EntregaCreateView(BaseCreateView):
    model = Entrega
    form_class = EntregaForm
    prefixo = "entrega"
    nome = "entrega"


class EntregaUpdateView(BaseUpdateView):
    model = Entrega
    form_class = EntregaEditForm
    prefixo = "entrega"
    nome = "entrega"


class EntregaDeleteView(BaseDeleteView):
    model = Entrega
    prefixo = "entrega"
    nome = "entrega"


@login_required
@require_POST
def entrega_status(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk)
    novo = request.POST.get("status", "")
    if novo not in dict(Entrega.STATUS):
        messages.error(request, "Status inválido.")
    elif entrega.status == "entregue":
        messages.error(request, "Esta entrega já foi concluída.")
    else:
        entrega.status = novo
        entrega.save()
        messages.success(request, "Status da entrega atualizado.")
    return redirect("entrega_lista")  

# ---------- Relatórios ----------

@login_required
@area_required("relatorios")
def relatorios_indice(request):
    return render(
        request,
        "relatorios/indice.html",
        {"relatorios": relatorios.RELATORIOS.items()},
    )


@login_required
@area_required("relatorios")
def relatorio(request, tipo):
    config = relatorios.RELATORIOS.get(tipo)
    if config is None:
        raise Http404("Relatório não encontrado.")

    hoje = timezone.localdate()
    inicio = relatorios.ler_data(request.GET.get("inicio"), hoje.replace(day=1))
    fim = relatorios.ler_data(request.GET.get("fim"), hoje)
    vendedor = request.GET.get("vendedor", "")
    if not vendedor.isdigit():
        vendedor = ""

    dados = config["func"](inicio, fim, vendedor)

    if request.GET.get("formato") == "csv":
        resposta = HttpResponse(content_type="text/csv; charset=utf-8")
        resposta["Content-Disposition"] = f'attachment; filename="relatorio_{tipo}.csv"'
        resposta.write("\ufeff")
        escritor = csv.writer(resposta, delimiter=";")
        escritor.writerow([config["titulo"]])
        if config["periodo"]:
            escritor.writerow([f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"])
        escritor.writerow([])
        escritor.writerow(dados["colunas"])
        escritor.writerows(dados["linhas"])
        escritor.writerow([])
        for rotulo, valor in dados["resumo"]:
            escritor.writerow([rotulo, valor])
        return resposta

    parametros = {"inicio": inicio.isoformat(), "fim": fim.isoformat()}
    if vendedor:
        parametros["vendedor"] = vendedor
    contexto = {
        "config": config,
        "dados": dados,
        "inicio": inicio,
        "fim": fim,
        "vendedor": vendedor,
        "vendedores": Funcionario.objects.filter(cargo="vendedor").order_by("nome"),
        "querystring": urlencode(parametros),
    }
    return render(request, "relatorios/relatorio.html", contexto)           