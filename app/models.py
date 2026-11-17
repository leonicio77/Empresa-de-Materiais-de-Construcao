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
    cargo = models.CharField(max_length=50)
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

        def __str__(self):
            return self.nome










