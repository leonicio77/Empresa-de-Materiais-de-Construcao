from django.db import models

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












