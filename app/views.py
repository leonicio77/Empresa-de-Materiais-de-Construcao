from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Categoria, Cliente, Fornecedor, Funcionario, Produto

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