from django.db import models
from django.core.exceptions import ValidationError
from django.db import models, transaction
from decimal import Decimal
from django.utils import timezone
from django.core.validators import MinValueValidator


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length = 18, unique = True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField("Endereço", max_length=255)
    email = models.EmailField(blank=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=18, unique=True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField("Endereço", max_length=255)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    CARGOS = [
        ("admin","Administrador"),
        ("gerente","Gerente"),
        ("vendedor","Vendedor"),
        ("caixa","Caixa"),
        ("estoquista","Estoquista"),
        ("entregador","Entregador"),
    ]

    nome = models.CharField(max_length=110)
    cpf = models.CharField(max_length=18, unique=True) 
    telefone = models.CharField(max_length=20)
    endereco = models.CharField("endereço", max_length=255,)
    email = models.EmailField(blank=True)
    cargo = models.CharField(max_length=20, choices=CARGOS)
    salario = models.DecimalField("salário", max_digits=10, decimal_places=2)
    percentual_comissao = models.DecimalField("% de comissao",max_digits=5, decimal_places=2,
    null=True, blank=True)

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"

    def __str__(self):
        return self.nome

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome    

class Produto(models.Model):
    nome = models.CharField(max_length=110)
    descricao = models.TextField("descrição", blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    qtd_estoque = models.PositiveIntegerField("quantidade em estoque", default=0)
    estoque_minimo = models.PositiveIntegerField("estoque mínimo", default=0)
    preco_unidade = models.DecimalField("preço por unidade", max_digits=10, decimal_places=2)
    m2 = models.DecimalField("m² por caixa", max_digits=6, decimal_places=2, null=True, blank=True)


    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    @property
    def abaixo_do_minimo(self):
        return self.qtd_estoque <= self.estoque_minimo

    def __str__(self):
        return self.nome

class Promocao(models.Model):
    nome = models.CharField(max_length=100)
    produtos = models.ManyToManyField(Produto, related_name="promocoes") 
    desconto = models.DecimalField("Desconto (%)", max_digits=5, decimal_places=2)
    data_inicio = models.DateField("Data de Inicio")
    data_fim = models.DateField("Data de Fim")

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"

    def __str__(self):
        return self.nome    

class MovimentacaoEstoque(models.Model):
    TIPOS = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
        ("ajuste", "Ajuste (perda/avaria/inventário)"),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "movimentação de estoque"
        verbose_name_plural = "movimentações de estoque"
        ordering = ["-data"]

    def clean(self):
        if self.pk is None and self.tipo != "entrada":
            if self.quantidade > self.produto.qtd_estoque:
                raise ValidationError("Estoque insuficiente para esta movimentação.")

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.tipo == "entrada":
                self.produto.qtd_estoque += self.quantidade
            else:
                self.produto.qtd_estoque -= self.quantidade
            self.produto.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.quantidade} - {self.produto}"

class Pedido(models.Model):
    STATUS = [
        ("aberto", "Aberto"),
        ("aprovado", "Aprovado"),
        ("faturado", "Faturado"),
        ("cancelado", "Cancelado"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    vendedor = models.ForeignKey(Funcionario,
    on_delete=models.PROTECT,
    limit_choices_to={"cargo": "vendedor"},
    )
    data = models.DateTimeField(auto_now_add=True)
    desconto = models.DecimalField(
        "desconto (R$)", max_digits=10, decimal_places=2, default=0
    )
    status = models.CharField(max_length=10, choices=STATUS, default="aberto")

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-data"]

    @property
    def subtotal(self):
        if self.pk is None:
            return 0
        return sum(item.subtotal for item in self.itens.all())

    @property
    def valor_total(self):
        return self.subtotal - self.desconto

    def __str__(self):
        return f"Pedido {self.pk} - {self.cliente}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="itens"
    )
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(
        "preço unitário", max_digits=10, decimal_places=2,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    @property
    def subtotal(self):
        if self.quantidade is None or self.preco_unitario is None:
            return 0
        return self.quantidade * self.preco_unitario

    def save(self, *args, **kwargs):
        if self.preco_unitario is None:
            self.preco_unitario = self.produto.preco_unidade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.produto}"  


class Venda(models.Model):
    FORMAS_PAGAMENTO = [
        ("dinheiro", "Dinheiro"),
        ("pix", "Pix"),
        ("debito", "Cartão de débito"),
        ("credito", "Cartão de crédito"),
        ("boleto", "Boleto"),
        
    ]
    STATUS = [
        ("concluida", "Concluída"),
        ("cancelada", "Cancelada"),
    ]

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.PROTECT,
        limit_choices_to={"status": "aprovado"},
    )
    motivo_cancelamento = models.CharField(
        "motivo do cancelamento", max_length=255, blank=True, default=""
    )
    data = models.DateTimeField(auto_now_add=True)
    forma_pagamento = models.CharField(
        "forma de pagamento", max_length=10, choices=FORMAS_PAGAMENTO
    )
    status = models.CharField(max_length=10, choices=STATUS, default="concluida")

    class Meta:
        verbose_name = "venda"
        verbose_name_plural = "vendas"
        ordering = ["-data"]

    @property
    def cliente(self):
        return self.pedido.cliente

    @property
    def vendedor(self):
        return self.pedido.vendedor

    @property
    def total_pago(self):
        if self.pk is None:
            return Decimal("0")
        return sum((p.valor for p in self.pagamentos.all()), Decimal("0"))

    @property
    def saldo_devedor(self):
        return self.valor_total - self.total_pago    

    @property
    def total_devolvido(self):
        if self.pk is None:
            return Decimal("0")
        return sum((d.valor for d in self.devolucoes.all()), Decimal("0"))

    @property
    def valor_total(self):
        return self.pedido.valor_total - self.total_devolvido

    def clean(self):
        if self.pk is None and self.pedido_id:
            itens = self.pedido.itens.all()
            if not itens:
                raise ValidationError("O pedido não tem itens.")
            totais = {}
            for item in itens:
                totais[item.produto] = totais.get(item.produto, 0) + item.quantidade
            for produto, qtd in totais.items():
                if qtd > produto.qtd_estoque:
                    raise ValidationError(
                        f"Estoque insuficiente de {produto} "
                        f"(pedido: {qtd}, disponível: {produto.qtd_estoque})."
                    )

    def save(self, *args, **kwargs):
        novo = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if novo:
                for item in self.pedido.itens.all():
                    produto = Produto.objects.get(pk=item.produto_id)
                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        tipo="saida",
                        quantidade=item.quantidade,
                        observacao=f"Venda {self.pk}",
                    )
                self.pedido.status = "faturado"
                self.pedido.save()

    def cancelar(self):
        if self.status != "concluida":
            raise ValidationError("Só vendas concluídas podem ser canceladas.")
        if not self.motivo_cancelamento.strip():
            raise ValidationError("Preencha o motivo do cancelamento na venda antes.")
        if self.pagamentos.exists():
            raise ValidationError(
                "A venda tem pagamentos. Estorne (exclua) os pagamentos antes."
            )
        if self.devolucoes.exists():
            raise ValidationError("A venda já tem devoluções e não pode ser cancelada.")
        with transaction.atomic():
            for item in self.pedido.itens.all():
                produto = Produto.objects.get(pk=item.produto_id)
                MovimentacaoEstoque.objects.create(
                    produto=produto,
                    tipo="entrada",
                    quantidade=item.quantidade,
                    observacao=f"Cancelamento da venda {self.pk}",
                )
            self.pedido.status = "cancelado"
            self.pedido.save()
            self.status = "cancelada"
            self.save()            

    def __str__(self):
        return f"Venda {self.pk} - {self.pedido.cliente}"  


class Compra(models.Model):
    STATUS = [
        ("pendente", "Pendente"),
        ("recebida", "Recebida"),
        ("cancelada", "Cancelada"),
    ]

    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT)
    data = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pendente")

    class Meta:
        verbose_name = "compra"
        verbose_name_plural = "compras"
        ordering = ["-data"]

    @property
    def valor_total(self):
        if self.pk is None:
            return 0
        return sum(item.subtotal for item in self.itens.all())

    def receber(self):
        if self.status != "pendente":
            raise ValidationError("Só é possível receber compras pendentes.")
        with transaction.atomic():
            for item in self.itens.all():
                produto = Produto.objects.get(pk=item.produto_id)
                MovimentacaoEstoque.objects.create(
                    produto=produto,
                    tipo="entrada",
                    quantidade=item.quantidade,
                    observacao=f"Compra {self.pk}",
                )
            self.status = "recebida"
            self.save()

    def cancelar(self):
        if self.status != "pendente":
            raise ValidationError("Só é possível cancelar compras pendentes.")
        self.status = "cancelada"
        self.save()

    def __str__(self):
        return f"Compra {self.pk} - {self.fornecedor}"


class ItemCompra(models.Model):
    compra = models.ForeignKey(
        Compra, on_delete=models.CASCADE, related_name="itens"
    )
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    custo = models.DecimalField("custo unitário", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "item da compra"
        verbose_name_plural = "itens da compra"

    @property
    def subtotal(self):
        if self.quantidade is None or self.custo is None:
            return 0
        return self.quantidade * self.custo

    def __str__(self):
        return f"{self.quantidade}x {self.produto}"    


class Despesa(models.Model):
    TIPOS = [
        ("agua", "Água"),
        ("luz", "Luz"),
        ("telefone", "Telefone"),
        ("internet", "Internet"),
        ("aluguel", "Aluguel"),
        ("salario", "Salário"),
        ("comissao", "Comissão"),
        ("outras", "Outras"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPOS)
    descricao = models.CharField("descrição", max_length=255, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    data_pagamento = models.DateField(
        "data de pagamento", null=True, blank=True
    )

    class Meta:
        verbose_name = "despesa"
        verbose_name_plural = "despesas"
        ordering = ["vencimento"]

    @property
    def status(self):
        if self.data_pagamento:
            return "Paga"
        if self.vencimento < timezone.localdate():
            return "Atrasada"
        return "A pagar"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.vencimento:%d/%m/%Y}"


class Comissao(models.Model):
    vendedor = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        limit_choices_to={"cargo": "vendedor"},
    )
    data_inicio = models.DateField("início do período")
    data_fim = models.DateField("fim do período")
    valor_vendas = models.DecimalField(
        "total vendido", max_digits=12, decimal_places=2,
        default=0, editable=False,
    )
    percentual = models.DecimalField(
        "% aplicado", max_digits=5, decimal_places=2,
        default=0, editable=False,
    )
    valor_comissao = models.DecimalField(
        "valor da comissão", max_digits=10, decimal_places=2,
        default=0, editable=False,
    )
    despesa = models.OneToOneField(
        Despesa, on_delete=models.PROTECT,
        null=True, editable=False,
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "comissão"
        verbose_name_plural = "comissões"
        ordering = ["-criada_em"]

    def clean(self):
        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError("A data final não pode ser anterior à inicial.")
            if self.vendedor_id:
                conflito = Comissao.objects.filter(
                    vendedor=self.vendedor,
                    data_inicio__lte=self.data_fim,
                    data_fim__gte=self.data_inicio,
                ).exclude(pk=self.pk)
                if conflito.exists():
                    raise ValidationError(
                        "Já existe comissão deste vendedor que cobre parte deste período."
                    )

    def save(self, *args, **kwargs):
        if self.pk is None:
            vendas = Venda.objects.filter(
                pedido__vendedor=self.vendedor,
                status="concluida",
                data__date__gte=self.data_inicio,
                data__date__lte=self.data_fim,
            )
            total = sum((v.valor_total for v in vendas), Decimal("0"))
            self.valor_vendas = total
            self.percentual = self.vendedor.percentual_comissao
            self.valor_comissao = (total * self.percentual / 100).quantize(
                Decimal("0.01")
            )
            with transaction.atomic():
                self.despesa = Despesa.objects.create(
                    tipo="comissao",
                    descricao=f"Comissão de {self.vendedor} "
                              f"({self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y})",
                    valor=self.valor_comissao,
                    vencimento=timezone.localdate(),
                )
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vendedor} - {self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}"  

class Entrega(models.Model):
    STATUS = [
        ("pendente", "Pendente"),
        ("em_rota", "Em rota"),
        ("entregue", "Entregue"),
        ("nao_entregue", "Não entregue"),
    ]

    venda = models.OneToOneField(
        Venda,
        on_delete=models.PROTECT,
        limit_choices_to={"status": "concluida"},
    )
    endereco = models.CharField("endereço de entrega", max_length=255, blank=True)
    data_prevista = models.DateField("data prevista")
    data_entrega = models.DateTimeField(
        "entregue em", null=True, blank=True, editable=False
    )
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entregador = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        limit_choices_to={"cargo": "entregador"},
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=15, choices=STATUS, default="pendente")

    class Meta:
        verbose_name = "entrega"
        verbose_name_plural = "entregas"
        ordering = ["data_prevista"]

    def save(self, *args, **kwargs):
        if not self.endereco:
            self.endereco = self.venda.cliente.endereco
        if self.status == "entregue" and self.data_entrega is None:
            self.data_entrega = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Entrega da venda {self.venda_id} - {self.get_status_display()}"  

class Pagamento(models.Model):
    FORMAS = [
        ("dinheiro", "Dinheiro"),
        ("pix", "Pix"),
        ("debito", "Cartão de débito"),
        ("credito", "Cartão de crédito"),
        ("boleto", "Boleto"),
    ]

    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="pagamentos",
        limit_choices_to={"status": "concluida"},
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    forma = models.CharField(max_length=10, choices=FORMAS)
    data = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"
        ordering = ["-data"]

    def clean(self):
        if self.pk is None and self.venda_id and self.valor is not None:
            if self.valor > self.venda.saldo_devedor:
                raise ValidationError(
                    f"O valor é maior que o saldo devedor "
                    f"(R$ {self.venda.saldo_devedor:.2f})."
                )

    def __str__(self):
        return f"Pagamento de R$ {self.valor} - venda {self.venda_id}"       

class Devolucao(models.Model):
    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="devolucoes",
        limit_choices_to={"status": "concluida"},
    )
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    motivo = models.CharField(max_length=255)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "devolução"
        verbose_name_plural = "devoluções"
        ordering = ["-data"]

    @property
    def valor(self):
        item = self.venda.pedido.itens.filter(produto=self.produto).first()
        if item is None or item.preco_unitario is None:
            return Decimal("0")
        return self.quantidade * item.preco_unitario

    def clean(self):
        if self.pk is None and self.venda_id and self.produto_id and self.quantidade:
            itens = self.venda.pedido.itens.filter(produto=self.produto)
            vendida = sum(i.quantidade for i in itens)
            if vendida == 0:
                raise ValidationError("Este produto não faz parte da venda.")
            ja_devolvida = sum(
                d.quantidade
                for d in self.venda.devolucoes.filter(produto=self.produto)
            )
            if self.quantidade > vendida - ja_devolvida:
                raise ValidationError(
                    f"Quantidade maior que a possível: vendida {vendida}, "
                    f"já devolvida {ja_devolvida}."
                )

    def save(self, *args, **kwargs):
        novo = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if novo:
                MovimentacaoEstoque.objects.create(
                    produto=Produto.objects.get(pk=self.produto_id),
                    tipo="entrada",
                    quantidade=self.quantidade,
                    observacao=f"Devolução da venda {self.venda_id}",
                )

    def __str__(self):
        return f"Devolução de {self.quantidade}x {self.produto} (venda {self.venda_id})"                                     












