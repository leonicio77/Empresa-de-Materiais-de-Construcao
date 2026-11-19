from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import Cliente


@login_required
def home(request):
    return render(request, "home.html")


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"

    def get_queryset(self):
        clientes = super().get_queryset().order_by("nome")
        busca = self.request.GET.get("q", "").strip()
        if busca:
            clientes = clientes.filter(
                Q(nome__icontains=busca) | Q(cpf_cnpj__icontains=busca)
            )
        return clientes

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["busca"] = self.request.GET.get("q", "")
        return contexto


class ClienteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Cliente
    fields = ["nome", "cpf_cnpj", "telefone", "endereco", "email"]
    template_name = "clientes/form.html"
    success_url = reverse_lazy("cliente_lista")
    success_message = "Cliente cadastrado com sucesso."


class ClienteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Cliente
    fields = ["nome", "cpf_cnpj", "telefone", "endereco", "email"]
    template_name = "clientes/form.html"
    success_url = reverse_lazy("cliente_lista")
    success_message = "Cliente atualizado com sucesso."


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = "clientes/confirmar_exclusao.html"
    success_url = reverse_lazy("cliente_lista")

    def form_valid(self, form):
        try:
            resposta = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Não é possível excluir: este cliente possui pedidos.",
            )
            return redirect("cliente_lista")
        messages.success(self.request, "Cliente excluído com sucesso.")
        return resposta