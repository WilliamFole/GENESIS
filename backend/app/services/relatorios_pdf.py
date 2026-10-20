"""PDF generators for relatorios using the SGE layouts."""
import io
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.utilizador import Utilizador

ACCENT = colors.HexColor("#1F5BA8")
HEADER_BG = colors.HexColor("#DCE4F0")
BORDER = colors.HexColor("#9FAEC2")
TEXT = colors.HexColor("#1F2933")
TEXT_MUTED = colors.HexColor("#44546A")
ROW_ALT = colors.HexColor("#F6F8FB")
ROW_BORDER = colors.HexColor("#D5DDE8")
FOOTER_TEXT = colors.HexColor("#5B6B67")
LOGO_HINT = colors.HexColor("#7A8CA3")

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm


def _fmt(v):
    try:
        return f"{float(v):,.2f}".replace(",", " ").replace(".", ",")
    except Exception:
        return str(v)


def _draw_header(c, empresa, titulo, emitido_em):
    y = PAGE_H - MARGIN

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.setDash(2, 2)
    c.rect(MARGIN, y - 72, 72, 72, fill=0, stroke=1)
    c.setDash()
    c.setFillColor(LOGO_HINT)
    c.setFont("Helvetica", 7)
    c.drawCentredString(MARGIN + 36, y - 38, "[LOGOTIPO]")

    x_info = MARGIN + 72 + 14
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    nome_emp = empresa.designacao if empresa else "[Nome da empresa]"
    c.drawString(x_info, y - 12, f"{nome_emp}, Lda")
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(x_info, y - 26, empresa.morada if empresa else "[Morada, cidade]")
    nuit = empresa.nuit if empresa else "[NUIT]"
    tel = (empresa.telefone if empresa else "") or ""
    c.drawString(x_info, y - 38, f"NUIT {nuit}" + (f" · Tel. {tel}" if tel else ""))

    titulo_x = PAGE_W - MARGIN
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(titulo_x, y - 16, titulo)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(titulo_x, y - 32, f"Emitido em {emitido_em} · Página 1 de 1")

    return y - 72 - 16


def _draw_box(c, x, y, w, h, titulo):
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(x, y - h, w, h, fill=0, stroke=1)
    c.setFillColor(HEADER_BG)
    c.rect(x, y - 14, w, 14, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 6, y - 10, titulo)


def _draw_table(c, x, y, widths, headers, rows, right_cols=(), special_first_row=None):
    total_w = sum(widths)
    th = 16

    c.setFillColor(ACCENT)
    c.rect(x, y - th, total_w, th, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    cx = x
    for i, h in enumerate(headers):
        if i in right_cols:
            c.drawRightString(cx + widths[i] - 4, y - th + 5, h)
        else:
            c.drawString(cx + 4, y - th + 5, h)
        cx += widths[i]
    y -= th

    if special_first_row:
        cells, right_idx = special_first_row
        rh = 14
        c.setFillColor(colors.white)
        c.rect(x, y - rh, total_w, rh, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 8)
        cx = x
        for i, cell in enumerate(cells):
            if i in right_idx:
                c.drawRightString(cx + widths[i] - 4, y - rh + 4, str(cell))
            else:
                c.drawString(cx + 4, y - rh + 4, str(cell))
            cx += widths[i]
        y -= rh

    rh = 14
    for idx, row in enumerate(rows):
        if idx % 2 == 1:
            c.setFillColor(ROW_ALT)
            c.rect(x, y - rh, total_w, rh, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica", 8)
        cx = x
        for i, cell in enumerate(row):
            if i in right_cols:
                c.drawRightString(cx + widths[i] - 4, y - rh + 4, str(cell))
            else:
                c.drawString(cx + 4, y - rh + 4, str(cell))
            cx += widths[i]
        y -= rh
        c.setStrokeColor(ROW_BORDER)
        c.setLineWidth(0.3)
        c.line(x, y, x + total_w, y)

    return y


def _draw_footer(c, empresa, utilizador):
    y = MARGIN + 20
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.5)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    c.setFillColor(FOOTER_TEXT)
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN, y - 10, "Processado por computador · SGE - FATURAÇÃO")
    nome_util = getattr(utilizador, "nome", None) or getattr(utilizador, "username", "—")
    c.drawRightString(PAGE_W - MARGIN, y - 10, f"Utilizador: {nome_util}")


def gerar_extrato_cliente_pdf(
    empresa: Empresa | None,
    cliente: Cliente,
    extrato: dict,
    aging: list[Decimal],
    utilizador: Utilizador,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Extrato {cliente.numero_formatado}")

    y = _draw_header(
        c, empresa, "EXTRATO DE CONTA CORRENTE",
        date.today().strftime("%d/%m/%Y"),
    )

    box_h = 56
    box_periodo_w = 170
    box_cliente_w = PAGE_W - 2 * MARGIN - box_periodo_w - 8
    box_periodo_x = PAGE_W - MARGIN - box_periodo_w

    _draw_box(c, MARGIN, y, box_cliente_w, box_h, "CLIENTE")
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + 8, y - 28, cliente.nome)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN + 8, y - 40, cliente.morada or "")
    c.drawString(MARGIN + 8, y - 50, f"NUIT {cliente.nuit}")

    _draw_box(c, box_periodo_x, y, box_periodo_w, box_h, "PERÍODO")
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 9)
    p = extrato["periodo"]
    c.drawString(box_periodo_x + 8, y - 28, f"De {p['inicio'].strftime('%d/%m/%Y')}")
    c.drawString(box_periodo_x + 8, y - 40, f"A {p['fim'].strftime('%d/%m/%Y')}")
    c.setFillColor(TEXT_MUTED)
    c.drawString(box_periodo_x + 8, y - 52, "Moeda: MZN")

    y -= box_h + 1

    total_w = PAGE_W - 2 * MARGIN
    raw_widths = [55, 83, 165, 69, 69, 69]
    ratio = total_w / sum(raw_widths)
    widths = [w * ratio for w in raw_widths]

    headers = ["Data", "Documento", "Descrição", "Débito", "Crédito", "Saldo"]
    rows = []
    for m in extrato["movimentos"]:
        rows.append([
            m["data"].strftime("%d/%m/%Y"),
            m["numero"] if m["numero"] else m["tipo"],  # <-- AQUI: Correção FT FT/1
            m["descricao"],
            _fmt(m["debito"]) if m["debito"] > 0 else "",
            _fmt(m["credito"]) if m["credito"] > 0 else "",
            _fmt(m["saldo"]),
        ])

    special = (
        [
            p["inicio"].strftime("%d/%m/%Y"),
            "Saldo transitado",
            "",
            "",
            "",
            _fmt(extrato["saldo_inicial"]),
        ],
        (3, 4, 5),
    )
    y = _draw_table(
        c, MARGIN, y, widths, headers, rows,
        right_cols=(3, 4, 5),
        special_first_row=special,
    )

    y -= 16

    totals_w = 200
    aging_w = total_w - totals_w - 8
    totals_x = PAGE_W - MARGIN - totals_w
    box_h2 = 84

    aging_labels = [
        "Por vencer",
        "Vencido até 30 dias",
        "Vencido 31 a 60 dias",
        "Vencido há mais de 60 dias",
    ]
    aging_rows = [[lbl, _fmt(aging[i])] for i, lbl in enumerate(aging_labels)]
    aging_widths = [aging_w - 80, 80]
    _draw_table(
        c, MARGIN, y, aging_widths,
        ["Antiguidade do saldo", "Valor (MZN)"],
        aging_rows, right_cols=(1,),
    )

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(totals_x, y - box_h2, totals_w, box_h2, fill=0, stroke=1)

    total_debito = sum((m["debito"] for m in extrato["movimentos"]), Decimal("0"))
    total_credito = sum((m["credito"] for m in extrato["movimentos"]), Decimal("0"))

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(totals_x + 8, y - 18, "Total débito")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 18, _fmt(total_debito))

    c.setFillColor(TEXT_MUTED)
    c.drawString(totals_x + 8, y - 36, "Total crédito")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 36, _fmt(total_credito))

    c.setFillColor(ACCENT)
    c.rect(totals_x, y - box_h2, totals_w, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(totals_x + 8, y - box_h2 + 10, "Saldo final (MZN)")
    c.drawRightString(totals_x + totals_w - 8, y - box_h2 + 10, _fmt(extrato["saldo_final"]))

    _draw_footer(c, empresa, utilizador)

    c.save()
    return buf.getvalue()


def gerar_relatorio_vendas_pdf(
    empresa: Empresa | None,
    filtros: dict,
    resumo_vendas: dict,
    utilizador: Utilizador,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Extrato de Vendas")

    y = _draw_header(
        c, empresa, "EXTRATO DE VENDAS",
        date.today().strftime("%d/%m/%Y"),
    )

    # Filtros box
    box_h = 32
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(MARGIN, y - box_h, PAGE_W - 2 * MARGIN, box_h, fill=0, stroke=1)
    c.setFillColor(HEADER_BG)
    c.rect(MARGIN, y - 14, PAGE_W - 2 * MARGIN, 14, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN + 6, y - 10, "FILTROS")

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    fy = y - 24
    c.drawString(MARGIN + 8, fy, f"Período: {filtros['periodo']}")
    c.drawString(MARGIN + 250, fy, "Moeda: MZN")

    y -= box_h + 1

    total_w = PAGE_W - 2 * MARGIN
    # Colunas: Cliente, Total Bruto, Total Líquido, Total IVA
    raw = [200, 80, 80, 80]
    ratio = total_w / sum(raw)
    widths = [w * ratio for w in raw]

    headers = ["Cliente", "Total Bruto (MZN)", "Total Líquido (MZN)", "Total IVA (MZN)"]
    rows = []
    for c_data in resumo_vendas["por_cliente"]:
        rows.append([
            c_data["nome"],
            _fmt(c_data["bruto"]),
            _fmt(c_data["liquido"]),
            _fmt(c_data["iva"]),
        ])

    y = _draw_table(c, MARGIN, y, widths, headers, rows, right_cols=(1, 2, 3))

    y -= 16

    totals_w = 250
    totals_x = PAGE_W - MARGIN - totals_w
    box_h2 = 90

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(totals_x, y - box_h2, totals_w, box_h2, fill=0, stroke=1)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(totals_x + 8, y - 18, "Total Bruto")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 18, _fmt(resumo_vendas["totais"]["bruto"]))

    c.setFillColor(TEXT_MUTED)
    c.drawString(totals_x + 8, y - 36, "Total Líquido (c/ NC)")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 36, _fmt(resumo_vendas["totais"]["liquido"]))
    
    c.setFillColor(TEXT_MUTED)
    c.drawString(totals_x + 8, y - 54, "Total IVA")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 54, _fmt(resumo_vendas["totais"]["iva"]))

    c.setFillColor(ACCENT)
    c.rect(totals_x, y - box_h2, totals_w, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(totals_x + 8, y - box_h2 + 10, f"Total de Docs: {resumo_vendas['totais']['documentos']}")
    c.drawRightString(totals_x + totals_w - 8, y - box_h2 + 10, "MZN")

    _draw_footer(c, empresa, utilizador)

    c.save()
    return buf.getvalue()

def gerar_extrato_faturas_pdf(
    empresa: Empresa | None,
    filtros: dict,
    docs_enriched: list[dict],
    resumo_estado: dict,
    totais: dict,
    utilizador: Utilizador,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Extrato de faturas")

    y = _draw_header(
        c, empresa, "EXTRATO DE FATURAS",
        date.today().strftime("%d/%m/%Y"),
    )

    box_h = 32
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(MARGIN, y - box_h, PAGE_W - 2 * MARGIN, box_h, fill=0, stroke=1)
    c.setFillColor(HEADER_BG)
    c.rect(MARGIN, y - 14, PAGE_W - 2 * MARGIN, 14, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN + 6, y - 10, "FILTROS")

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    fy = y - 24
    c.drawString(MARGIN + 8, fy, f"Período: {filtros['periodo']}")
    c.drawString(MARGIN + 200, fy, f"Cliente: {filtros['cliente']}")
    c.drawString(MARGIN + 340, fy, f"Estado: {filtros['estado']}")
    c.drawString(MARGIN + 440, fy, "Moeda: MZN")

    y -= box_h + 1

    total_w = PAGE_W - 2 * MARGIN
    raw = [80, 55, 55, 110, 55, 50, 55, 50]
    ratio = total_w / sum(raw)
    widths = [w * ratio for w in raw]

    headers = ["Documento", "Data", "Vencimento", "Cliente", "Líquido", "IVA", "Total", "Estado"]
    rows = []
    for d in docs_enriched:
        rows.append([
            d["documento"],
            d["data"],
            d["vencimento"],
            d["cliente"],
            _fmt(d["liquido"]),
            _fmt(d["iva"]),
            _fmt(d["total"]),
            d["estado"],
        ])

    y = _draw_table(c, MARGIN, y, widths, headers, rows, right_cols=(4, 5, 6))

    y -= 16

    totals_w = 200
    resumo_w = total_w - totals_w - 8
    totals_x = PAGE_W - MARGIN - totals_w
    box_h2 = 90

    resumo_rows = [
        ["Pagas", str(resumo_estado["pagas"]["n"]), _fmt(resumo_estado["pagas"]["total"])],
        ["Em aberto", str(resumo_estado["abertas"]["n"]), _fmt(resumo_estado["abertas"]["total"])],
        ["Vencidas", str(resumo_estado["vencidas"]["n"]), _fmt(resumo_estado["vencidas"]["total"])],
    ]
    resumo_widths = [resumo_w - 130, 60, 70]
    _draw_table(
        c, MARGIN, y, resumo_widths,
        ["Resumo por estado", "Nº docs.", "Total (MZN)"],
        resumo_rows, right_cols=(1, 2),
    )

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(totals_x, y - box_h2, totals_w, box_h2, fill=0, stroke=1)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(totals_x + 8, y - 18, "Total líquido")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 18, _fmt(totais["liquido"]))

    c.setFillColor(TEXT_MUTED)
    c.drawString(totals_x + 8, y - 36, "Total IVA")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 36, _fmt(totais["iva"]))

    c.setFillColor(ACCENT)
    c.rect(totals_x, y - box_h2, totals_w, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(totals_x + 8, y - box_h2 + 10, "Total (MZN)")
    c.drawRightString(totals_x + totals_w - 8, y - box_h2 + 10, _fmt(totais["total"]))

    _draw_footer(c, empresa, utilizador)

    c.save()
    return buf.getvalue()


def gerar_extrato_geral_pdf(
    empresa: Empresa | None,
    filtros: dict,
    clientes: list[dict],
    totais: dict,
    utilizador: Utilizador,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Extrato geral de clientes")

    y = _draw_header(
        c, empresa, "EXTRATO GERAL DE CLIENTES",
        date.today().strftime("%d/%m/%Y"),
    )

    # Filtros box
    box_h = 32
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(MARGIN, y - box_h, PAGE_W - 2 * MARGIN, box_h, fill=0, stroke=1)
    c.setFillColor(HEADER_BG)
    c.rect(MARGIN, y - 14, PAGE_W - 2 * MARGIN, 14, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(MARGIN + 6, y - 10, "FILTROS")

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    fy = y - 24
    c.drawString(MARGIN + 8, fy, f"Período: {filtros['periodo']}")
    c.drawString(MARGIN + 250, fy, "Moeda: MZN")

    y -= box_h + 1

    total_w = PAGE_W - 2 * MARGIN
    raw = [150, 70, 70, 70, 70, 70]
    ratio = total_w / sum(raw)
    widths = [w * ratio for w in raw]

    headers = ["Clientes", "NUIT", "Saldo Inicial", "Total Debito", "Total Credito", "Saldo Final"]

    # Desenhar o cabeçalho da tabela
    th = 16
    c.setFillColor(ACCENT)
    c.rect(MARGIN, y - th, total_w, th, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    cx = MARGIN
    for i, h in enumerate(headers):
        if i in (2, 3, 4, 5):
            c.drawRightString(cx + widths[i] - 4, y - th + 5, h)
        else:
            c.drawString(cx + 4, y - th + 5, h)
        cx += widths[i]
    y -= th

    rh = 14
    for cli in clientes:
        # Linha do Cliente (Negrito, fundo diferente)
        c.setFillColor(colors.HexColor("#E8EEF5"))
        c.rect(MARGIN, y - rh, total_w, rh, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 8)
        
        row_cells = [
            cli["nome"],
            cli["nuit"],
            _fmt(cli["saldo_inicial"]),
            _fmt(cli["total_debito"]),
            _fmt(cli["total_credito"]),
            _fmt(cli["saldo_final"]),
        ]
        cx = MARGIN
        for i, cell in enumerate(row_cells):
            if i in (2, 3, 4, 5):
                c.drawRightString(cx + widths[i] - 4, y - rh + 4, str(cell))
            else:
                c.drawString(cx + 4, y - rh + 4, str(cell))
            cx += widths[i]
        y -= rh
        c.setStrokeColor(ROW_BORDER)
        c.line(MARGIN, y, MARGIN + total_w, y)

        # Linhas dos Documentos
        for m in cli["movimentos"]:
            c.setFillColor(colors.white)
            c.rect(MARGIN, y - rh, total_w, rh, fill=1, stroke=0)
            c.setFillColor(TEXT)
            c.setFont("Helvetica", 8)
            
            doc_label = f"{m['numero']} ({m['data'].strftime('%d/%m/%Y')})" # <-- AQUI: Correção FT FT/1
            row_cells = [
                doc_label,
                "",
                "",
                _fmt(m["debito"]) if m["debito"] > 0 else "",
                _fmt(m["credito"]) if m["credito"] > 0 else "",
                "",
            ]
            cx = MARGIN
            for i, cell in enumerate(row_cells):
                if i in (2, 3, 4, 5):
                    c.drawRightString(cx + widths[i] - 4, y - rh + 4, str(cell))
                else:
                    c.drawString(cx + 4, y - rh + 4, str(cell))
                cx += widths[i]
            y -= rh
            c.setStrokeColor(ROW_BORDER)
            c.line(MARGIN, y, MARGIN + total_w, y)

    y -= 16

    totals_w = 250
    totals_x = PAGE_W - MARGIN - totals_w
    box_h2 = 70

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(totals_x, y - box_h2, totals_w, box_h2, fill=0, stroke=1)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(totals_x + 8, y - 18, "Total Debito")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 18, _fmt(totais["debito"]))

    c.setFillColor(TEXT_MUTED)
    c.drawString(totals_x + 8, y - 36, "Total Credito")
    c.setFillColor(TEXT)
    c.drawRightString(totals_x + totals_w - 8, y - 36, _fmt(totais["credito"]))

    c.setFillColor(ACCENT)
    c.rect(totals_x, y - box_h2, totals_w, 30, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(totals_x + 8, y - box_h2 + 10, "Saldo Final (MZN)")
    c.drawRightString(totals_x + totals_w - 8, y - box_h2 + 10, _fmt(totais["saldo_final"]))

    _draw_footer(c, empresa, utilizador)

    c.save()
    return buf.getvalue()