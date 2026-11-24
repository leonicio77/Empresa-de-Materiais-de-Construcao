from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

EMPRESA = "Empresa Comercial de Materiais de Construção"
AZUL = colors.HexColor("#1f3a5f")
CINZA = colors.HexColor("#c9ced6")
ZEBRA = colors.HexColor("#f5f7fa")


def _estilo_tabela(direita_a_partir_de):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, CINZA),
        ("ALIGN", (direita_a_partir_de, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
    ])


def gerar_documento(titulo, numero, info, itens, totais,
                    pagamentos=None, observacao=""):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"{titulo} {numero}",
    )
    estilos = getSampleStyleSheet()
    emitido = timezone.localtime().strftime("%d/%m/%Y %H:%M")

    elementos = [
        Paragraph(escape(EMPRESA), estilos["Title"]),
        Paragraph(f"{escape(titulo)} nº {numero}", estilos["Heading2"]),
        Paragraph(f"Emitido em {emitido}", estilos["Normal"]),
        Spacer(1, 0.4 * cm),
    ]

    for rotulo, valor in info:
        elementos.append(
            Paragraph(f"<b>{escape(rotulo)}:</b> {escape(str(valor))}", estilos["Normal"])
        )
    elementos.append(Spacer(1, 0.5 * cm))

    linhas = [["Produto", "Qtd", "Preço unit.", "Subtotal"]]
    for nome, quantidade, preco, subtotal in itens:
        linhas.append([
            Paragraph(escape(nome), estilos["Normal"]),
            str(quantidade),
            f"R$ {preco}",
            f"R$ {subtotal}",
        ])
    tabela_itens = Table(
        linhas, colWidths=[8.5 * cm, 2 * cm, 3 * cm, 3.5 * cm], repeatRows=1
    )
    tabela_itens.setStyle(_estilo_tabela(1))
    elementos += [tabela_itens, Spacer(1, 0.4 * cm)]

    tabela_totais = Table(totais, colWidths=[13.5 * cm, 3.5 * cm])
    tabela_totais.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, AZUL),
    ]))
    elementos.append(tabela_totais)

    if pagamentos is not None:
        elementos += [
            Spacer(1, 0.6 * cm),
            Paragraph("Pagamentos", estilos["Heading3"]),
        ]
        if pagamentos:
            linhas_pg = [["Data", "Forma", "Valor"]]
            linhas_pg += [[data, forma, f"R$ {valor}"] for data, forma, valor in pagamentos]
            tabela_pg = Table(linhas_pg, colWidths=[4 * cm, 8 * cm, 5 * cm])
            tabela_pg.setStyle(_estilo_tabela(2))
            elementos.append(tabela_pg)
        else:
            elementos.append(Paragraph("Nenhum pagamento registrado.", estilos["Normal"]))

    if observacao:
        elementos += [
            Spacer(1, 0.8 * cm),
            Paragraph(f"<i>{escape(observacao)}</i>", estilos["Normal"]),
        ]

    documento.build(elementos)
    return buffer.getvalue()