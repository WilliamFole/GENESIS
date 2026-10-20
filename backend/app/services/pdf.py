from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import settings
from app.models.documento import Documento
from app.models.empresa import Empresa

# ---------- Cores do layout ----------
ACCENT = colors.HexColor("#1F5BA8")
ACCENT_SOFT = colors.HexColor("#CFE0F5")
SOFT_BG = colors.HexColor("#F6F8FB")
LINE_BG = colors.HexColor("#F6F8FB")
HEADER_BG = colors.HexColor("#DCE4F0")
BORDER = colors.HexColor("#B8C4D4")
TEXT = colors.HexColor("#1F2933")
TEXT_MUTED = colors.HexColor("#44546A")
RED_WARN = colors.HexColor("#B91C1C")

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm


# ---------- Utilitarios ----------

_UNIDADES = ["", "um", "dois", "tres", "quatro", "cinco", "seis", "sete", "oito", "nove",
             "dez", "onze", "doze", "treze", "catorze", "quinze", "dezasseis",
             "dezassete", "dezoito", "dezanove"]
_DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta",
            "setenta", "oitenta", "noventa"]
_CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
             "seiscentos", "setecentos", "oitocentos", "novecentos"]


def _grupo(n: int) -> str:
    if n == 0:
        return "zero"
    if n == 100:
        return "cem"
    partes = []
    if n >= 100:
        partes.append(_CENTENAS[n // 100])
        n %= 100
    if n >= 20:
        d = _DEZENAS[n // 10]
        u = n % 10
        partes.append(d + (" e " + _UNIDADES[u] if u else ""))
    elif n > 0:
        partes.append(_UNIDADES[n])
    return " e ".join(partes)


def valor_por_extenso(v: Decimal) -> str:
    inteiro = int(v)
    cent = int(round((v - inteiro) * 100))
    partes = []
    if inteiro == 0:
        partes.append("zero")
    else:
        milhoes = inteiro // 1_000_000
        milhares = (inteiro % 1_000_000) // 1_000
        resto = inteiro % 1_000
        if milhoes:
            partes.append(_grupo(milhoes) + (" milhao" if milhoes == 1 else " milhoes"))
        if milhares:
            partes.append(_grupo(milhares) + " mil")
        if resto:
            partes.append(_grupo(resto))
    texto = " e ".join(partes) + (" meticais" if inteiro != 1 else " metical")
    if cent:
        texto += f" e {_grupo(cent)} centavos"
    return texto[0].upper() + texto[1:]


def _fmt(v: Decimal) -> str:
    try:
        n = float(v)
    except Exception:
        return str(v)
    return f"{n:,.2f}".replace(",", " ").replace(".", ",")


def _draw_linha(c: canvas.Canvas, x1, y, x2, color=BORDER, w=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(w)
    c.line(x1, y, x2, y)


def _draw_caixa(c: canvas.Canvas, x, y, w, h, fill=None, stroke=BORDER):
    if fill:
        c.setFillColor(fill)
        c.rect(x, y, w, h, fill=1, stroke=0)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h, fill=0, stroke=1)


def _draw_qr(c: canvas.Canvas, url: str, x, y, size):
    qr = qrcode.QRCode(version=2, box_size=4, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    # Resolvido o aviso do Pylance no .save()
    img.save(buf, "PNG")  # type: ignore
    buf.seek(0)
    c.drawImage(
        __import__("reportlab.lib.utils", fromlist=["ImageReader"]).ImageReader(buf),
        x, y, width=size, height=size,
    )


def _draw_logo(c: canvas.Canvas, empresa: Empresa | None, x, y, w, h):
    if empresa and empresa.logotipo_path:
        base = Path(__file__).resolve().parents[2] / "uploads" / "logotipos"
        caminho = base / empresa.logotipo_path
        if caminho.exists():
            try:
                c.drawImage(
                    str(caminho), x, y, width=w, height=h,
                    preserveAspectRatio=True, anchor="c",
                )
                return
            except Exception:
                pass
    c.setStrokeColor(BORDER)
    c.setDash(2, 2)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + w / 2, y + h / 2 - 2, "[LOGOTIPO]")


def _desenhar_cabecalho(c: canvas.Canvas, doc: Documento, empresa: Empresa | None, via: str, y):
    logo_w, logo_h = 30 * mm, 20 * mm
    _draw_logo(c, empresa, MARGIN, y - logo_h, logo_w, logo_h)

    x_info = MARGIN + logo_w + 6 * mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_info, y - 5 * mm, empresa.designacao if empresa else "[Nome da empresa], Lda")

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    linha_y = y - 10 * mm
    c.drawString(x_info, linha_y, empresa.morada if empresa else "[Morada]")
    linha_y -= 4 * mm
    nuit = empresa.nuit if empresa else "[NUIT]"
    tel = empresa.telefone if empresa else ""
    c.drawString(x_info, linha_y, f"NUIT {nuit}" + (f" · Tel. {tel}" if tel else ""))
    linha_y -= 4 * mm
    extra = []
    if empresa and empresa.email:
        extra.append(empresa.email)
    c.drawString(x_info, linha_y, " · ".join(extra) if extra else "")

    titulo_x = PAGE_W - MARGIN
    c.setFillColor(ACCENT)

    titulos = {
        "FT": "FATURA",
        "VD": "VENDA A DINHEIRO",
        "FS": "FATURA SIMPLIFICADA",
        "NC": "NOTA DE CRÉDITO",
        "ND": "NOTA DE DÉBITO",
        "RC": "RECIBO",
        "COT": "COTAÇÃO",
        "PRO": "PROFORMA",
        "GR": "GUIA DE REMESSA"
    }
    tipo_str = doc.tipo_documento.value if hasattr(doc.tipo_documento, 'value') else str(doc.tipo_documento)
    titulo_doc = titulos.get(tipo_str.upper(), "DOCUMENTO")
    
    # Ajuste dinâmico do tamanho da fonte
    if len(titulo_doc) > 12:
        c.setFont("Helvetica-Bold", 14)
    elif len(titulo_doc) > 8:
        c.setFont("Helvetica-Bold", 18)
    else:
        c.setFont("Helvetica-Bold", 24)
        
    c.drawRightString(titulo_x, y - 8 * mm, titulo_doc)

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(titulo_x, y - 14 * mm, doc.numero_formatado or "RASCUNHO")

    badge_w, badge_h = 30 * mm, 6 * mm
    badge_x = titulo_x - badge_w
    badge_y = y - 22 * mm
    _draw_caixa(c, badge_x, badge_y, badge_w, badge_h, fill=ACCENT if doc.fiscal else RED_WARN, stroke=ACCENT if doc.fiscal else RED_WARN)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 1.8 * mm, via)

    if not doc.fiscal:
        c.setFillColor(RED_WARN)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(titulo_x, y - 26 * mm, "*** Este documento não serve de fatura ***")

    y = y - 32 * mm
    _draw_linha(c, MARGIN, y, PAGE_W - MARGIN, color=BORDER)
    return y


# ---------- Layout de Recibo ----------


def _desenhar_recibo(c: canvas.Canvas, doc: Documento, empresa: Empresa | None, via: str) -> None:
    y = PAGE_H - MARGIN
    y = _desenhar_cabecalho(c, doc, empresa, via, y)

    box_y = y - 28 * mm
    box_w = (PAGE_W - 2 * MARGIN - 6 * mm) / 2
    box_cli_x = MARGIN
    box_doc_x = MARGIN + box_w + 6 * mm

    _draw_caixa(c, box_cli_x, box_y, box_w, 26 * mm, fill=colors.white)
    c.setFillColor(HEADER_BG)
    c.rect(box_cli_x, box_y + 22 * mm, box_w, 4 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(box_cli_x + 3 * mm, box_y + 23 * mm, "RECEBEMOS DE")
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(box_cli_x + 3 * mm, box_y + 17 * mm, doc.cliente_nome or "[Nome do cliente]")
    c.setFont("Helvetica", 8.5)
    c.drawString(box_cli_x + 3 * mm, box_y + 12.5 * mm, doc.cliente_morada or "[Morada do cliente]")
    c.drawString(box_cli_x + 3 * mm, box_y + 8 * mm, f"NUIT {doc.cliente_nuit or '[NUIT]'}")

    _draw_caixa(c, box_doc_x, box_y, box_w, 26 * mm, fill=colors.white)
    c.setFillColor(HEADER_BG)
    c.rect(box_doc_x, box_y + 22 * mm, box_w, 4 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(box_doc_x + 3 * mm, box_y + 23 * mm, "PAGAMENTO")

    c.setFont("Helvetica", 8.5)
    info = [
        ("Data", doc.data_documento.strftime("%d/%m/%Y") if doc.data_documento else "—"),
        ("Forma de pagamento", "Vários"),
        ("Referência", "—"),
        ("Moeda", "MZN"),
    ]
    info_y = box_y + 17 * mm
    for label, valor in info:
        c.setFillColor(TEXT_MUTED)
        c.drawString(box_doc_x + 3 * mm, info_y, label)
        c.setFillColor(TEXT)
        c.drawRightString(box_doc_x + box_w - 3 * mm, info_y, str(valor))
        info_y -= 4 * mm

    y = box_y - 8 * mm
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, y, "DOCUMENTOS LIQUIDADOS")
    
    y -= 4 * mm
    col_widths = [40 * mm, 30 * mm, 30 * mm, None, None]
    col_widths[3] = 30 * mm
    col_widths[4] = PAGE_W - 2 * MARGIN - sum(w for w in col_widths if w)
    headers = ["Documento", "Data", "Vencimento", "Total", "Valor liquidado"]
    
    th = 8 * mm
    c.setFillColor(ACCENT)
    c.rect(MARGIN, y - th, PAGE_W - 2 * MARGIN, th, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    x = MARGIN
    for w, h in zip(col_widths, headers):
        if h in ("Total", "Valor liquidado"):
            c.drawRightString(x + w - 2 * mm, y - th + 2.5 * mm, h)
        else:
            c.drawString(x + 2 * mm, y - th + 2.5 * mm, h)
        x += w
    y -= th

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    for idx, linha in enumerate(doc.linhas):
        rh = 7 * mm
        if idx % 2 == 1:
            c.setFillColor(LINE_BG)
            c.rect(MARGIN, y - rh, PAGE_W - 2 * MARGIN, rh, fill=1, stroke=0)
            c.setFillColor(TEXT)
        
        x = MARGIN
        c.drawString(x + 2 * mm, y - rh + 2.4 * mm, linha.codigo or "—")
        x += col_widths[0]
        c.drawString(x + 2 * mm, y - rh + 2.4 * mm, doc.data_documento.strftime("%d/%m/%Y") if doc.data_documento else "—")
        x += col_widths[1]
        c.drawString(x + 2 * mm, y - rh + 2.4 * mm, "—")
        x += col_widths[2]
        c.drawRightString(x + col_widths[3] - 2 * mm, y - rh + 2.4 * mm, _fmt(linha.total_linha))
        x += col_widths[3]
        c.drawRightString(x + col_widths[4] - 2 * mm, y - rh + 2.4 * mm, _fmt(linha.total_linha))
        
        y -= rh
        _draw_linha(c, MARGIN, y, PAGE_W - MARGIN, color=BORDER, w=0.3)

    y -= 10 * mm
    tot_w = 90 * mm
    tot_x = PAGE_W - MARGIN - tot_w
    tot_h = 10 * mm
    
    c.setFillColor(ACCENT)
    c.rect(tot_x, y - tot_h, tot_w, tot_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(tot_x + 4 * mm, y - tot_h + 3.5 * mm, "Total recebido (MZN)")
    c.drawRightString(tot_x + tot_w - 4 * mm, y - tot_h + 3.5 * mm, _fmt(doc.total))

    y = y - tot_h - 8 * mm
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(MARGIN, y, "Valor por extenso: " + valor_por_extenso(doc.total))

    y = MARGIN + 25 * mm
    _draw_linha(c, MARGIN, y, MARGIN + 80 * mm, color=BORDER)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(MARGIN + 40 * mm, y - 4 * mm, "Assinatura do recebedor")

    _draw_linha(c, PAGE_W - MARGIN - 80 * mm, y, PAGE_W - MARGIN, color=BORDER)
    c.drawCentredString(PAGE_W - MARGIN - 40 * mm, y - 4 * mm, "Carimbo da empresa")

    y = MARGIN
    _draw_linha(c, MARGIN, y + 4 * mm, PAGE_W - MARGIN, color=ACCENT, w=1)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 7.5)
    cert = empresa.numero_certificacao if empresa and empresa.numero_certificacao else "[Nº de certificacao]"
    c.drawString(MARGIN, y, f"Processado por computador · SGE - FATURACAO · {cert}")
    c.drawRightString(PAGE_W - MARGIN, y, f"Pagina 1 de 1")


# ---------- Layout de Fatura (Geral) ----------


def _desenhar_pagina(c: canvas.Canvas, doc: Documento, empresa: Empresa | None, via: str) -> None:
    y = PAGE_H - MARGIN
    y = _desenhar_cabecalho(c, doc, empresa, via, y)

    box_y = y - 28 * mm
    box_w = (PAGE_W - 2 * MARGIN - 6 * mm) / 2
    box_cli_x = MARGIN
    box_doc_x = MARGIN + box_w + 6 * mm

    _draw_caixa(c, box_cli_x, box_y, box_w, 26 * mm, fill=colors.white)
    c.setFillColor(HEADER_BG)
    c.rect(box_cli_x, box_y + 22 * mm, box_w, 4 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(box_cli_x + 3 * mm, box_y + 23 * mm, "CLIENTE")
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(box_cli_x + 3 * mm, box_y + 17 * mm, doc.cliente_nome)
    c.setFont("Helvetica", 8.5)
    c.drawString(box_cli_x + 3 * mm, box_y + 12.5 * mm, doc.cliente_morada)
    c.drawString(box_cli_x + 3 * mm, box_y + 8 * mm, f"NUIT {doc.cliente_nuit}")

    _draw_caixa(c, box_doc_x, box_y, box_w, 26 * mm, fill=colors.white)
    c.setFillColor(HEADER_BG)
    c.rect(box_doc_x, box_y + 22 * mm, box_w, 4 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(box_doc_x + 3 * mm, box_y + 23 * mm, "DOCUMENTO")

    c.setFont("Helvetica", 8.5)
    info = [
        ("Data", doc.data_documento.strftime("%d/%m/%Y") if doc.data_documento else "—"),
        ("Vencimento", doc.data_vencimento.strftime("%d/%m/%Y") if doc.data_vencimento else "—"),
        ("Condicao de pagamento", doc.condicao_pagamento or "—"),
        ("Moeda", "MZN"),
    ]
    info_y = box_y + 17 * mm
    for label, valor in info:
        c.setFillColor(TEXT_MUTED)
        c.drawString(box_doc_x + 3 * mm, info_y, label)
        c.setFillColor(TEXT)
        c.drawRightString(box_doc_x + box_w - 3 * mm, info_y, str(valor))
        info_y -= 4 * mm

    y = box_y - 6 * mm
    col_widths = [20 * mm, 70 * mm, 12 * mm, 26 * mm, 12 * mm, 12 * mm, None]
    total_fixed = sum(w for w in col_widths if w)
    col_widths[-1] = PAGE_W - 2 * MARGIN - total_fixed
    headers = ["Artigo", "Descricao", "Qtd.", "Preco unit.", "Desc.%", "IVA%", "Valor"]

    th = 7 * mm
    c.setFillColor(ACCENT)
    c.rect(MARGIN, y - th, PAGE_W - 2 * MARGIN, th, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    x = MARGIN
    for w, h in zip(col_widths, headers):
        if h in ("Qtd.", "Preco unit.", "Desc.%", "IVA%", "Valor"):
            c.drawRightString(x + w - 2 * mm, y - th + 2.2 * mm, h)
        else:
            c.drawString(x + 2 * mm, y - th + 2.2 * mm, h)
        x += w
    y -= th

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    for idx, linha in enumerate(doc.linhas):
        rh = 7 * mm
        if idx % 2 == 1:
            c.setFillColor(LINE_BG)
            c.rect(MARGIN, y - rh, PAGE_W - 2 * MARGIN, rh, fill=1, stroke=0)
            c.setFillColor(TEXT)
        x = MARGIN
        c.setFont("Helvetica", 8)
        c.drawString(x + 2 * mm, y - rh + 2.4 * mm, linha.codigo)
        x += col_widths[0]
        c.drawString(x + 2 * mm, y - rh + 2.4 * mm, linha.descricao[:50])
        x += col_widths[1]
        c.drawRightString(x + col_widths[2] - 2 * mm, y - rh + 2.4 * mm, str(int(linha.quantidade)))
        x += col_widths[2]
        c.drawRightString(x + col_widths[3] - 2 * mm, y - rh + 2.4 * mm, _fmt(linha.preco_unitario))
        x += col_widths[3]
        c.drawRightString(x + col_widths[4] - 2 * mm, y - rh + 2.4 * mm, f"{linha.desconto_percentual:g}")
        x += col_widths[4]
        c.drawRightString(x + col_widths[5] - 2 * mm, y - rh + 2.4 * mm, f"{linha.taxa_iva:g}")
        x += col_widths[5]
        c.drawRightString(x + col_widths[6] - 2 * mm, y - rh + 2.4 * mm, _fmt(linha.total_linha))
        y -= rh
        _draw_linha(c, MARGIN, y, PAGE_W - MARGIN, color=BORDER, w=0.3)

    y -= 8 * mm

    iva_box_w = 90 * mm
    iva_box_h = 18 * mm
    _draw_caixa(c, MARGIN, y - iva_box_h, iva_box_w, iva_box_h, fill=colors.white)
    c.setFillColor(HEADER_BG)
    c.rect(MARGIN, y - 6 * mm, iva_box_w, 5 * mm, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 3 * mm, y - 5 * mm, "Resumo de IVA")
    c.drawRightString(MARGIN + 48 * mm, y - 5 * mm, "Incidencia")
    c.drawRightString(MARGIN + 65 * mm, y - 5 * mm, "Taxa")
    c.drawRightString(MARGIN + iva_box_w - 3 * mm, y - 5 * mm, "Valor IVA")

    por_taxa: dict[Decimal, dict] = {}
    for l in doc.linhas:
        t = l.taxa_iva
        if t not in por_taxa:
            por_taxa[t] = {"base": Decimal("0"), "iva": Decimal("0")}
        por_taxa[t]["base"] += l.base_tributavel
        por_taxa[t]["iva"] += l.valor_iva

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8.5)
    ly = y - 10 * mm
    for taxa, vals in sorted(por_taxa.items(), reverse=True):
        c.drawString(MARGIN + 3 * mm, ly, f"IVA {taxa:g}%")
        c.drawRightString(MARGIN + 48 * mm, ly, _fmt(vals["base"]))
        c.drawRightString(MARGIN + 65 * mm, ly, f"{taxa:g}%")
        c.drawRightString(MARGIN + iva_box_w - 3 * mm, ly, _fmt(vals["iva"]))
        ly -= 5 * mm

    tot_w = 90 * mm
    tot_x = PAGE_W - MARGIN - tot_w
    tot_h = 26 * mm
    _draw_caixa(c, tot_x, y - tot_h, tot_w, tot_h, fill=colors.white)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(tot_x + 3 * mm, y - 6 * mm, "Total liquido")
    c.drawRightString(tot_x + tot_w - 3 * mm, y - 6 * mm, _fmt(doc.subtotal))
    c.drawString(tot_x + 3 * mm, y - 11 * mm, "Descontos")
    c.drawRightString(tot_x + tot_w - 3 * mm, y - 11 * mm, _fmt(doc.desconto_global_valor))
    c.drawString(tot_x + 3 * mm, y - 16 * mm, "IVA")
    c.drawRightString(tot_x + tot_w - 3 * mm, y - 16 * mm, _fmt(doc.total_iva))

    c.setFillColor(ACCENT)
    c.rect(tot_x, y - tot_h, tot_w, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(tot_x + 3 * mm, y - tot_h + 2.5 * mm, f"Total (MZN)")
    c.drawRightString(tot_x + tot_w - 3 * mm, y - tot_h + 2.5 * mm, _fmt(doc.total))

    y -= tot_h + 6 * mm
    banco_box_h = 14 * mm
    _draw_caixa(c, MARGIN, y - banco_box_h, 90 * mm, banco_box_h, fill=colors.white)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 3 * mm, y - 4 * mm, "DADOS BANCARIOS")
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    banco = (doc.banco or "[Banco]")
    nib = doc.nib or "[NIB]"
    conta = doc.conta or "[Conta]"
    c.drawString(MARGIN + 3 * mm, y - 8 * mm, f"{banco} · NIB {nib}")
    c.drawString(MARGIN + 3 * mm, y - 12 * mm, f"Conta {conta}")

    obs_y = y - banco_box_h - 3 * mm
    obs_box_h = 16 * mm
    _draw_caixa(c, MARGIN, obs_y - obs_box_h, PAGE_W - 2 * MARGIN, obs_box_h, fill=colors.white)
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 3 * mm, obs_y - 5 * mm, "OBSERVACOES")
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 8)
    if doc.observacoes:
        txt = c.beginText(MARGIN + 3 * mm, obs_y - 9 * mm)
        txt.setFont("Helvetica", 8)
        for linha_txt in doc.observacoes.splitlines()[:3]:
            txt.textLine(linha_txt[:120])
        c.drawText(txt)

    y = obs_y - obs_box_h - 4 * mm
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(MARGIN, y, "Valor por extenso: " + valor_por_extenso(doc.total))

    y = MARGIN + 6 * mm
    qr_size = 22 * mm
    if doc.hash and doc.fiscal:
        url = f"{settings.PUBLIC_VERIFY_BASE_URL}/v/{doc.hash[:16]}"
        _draw_qr(c, url, MARGIN, y, qr_size)
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 7)
        c.drawString(MARGIN + qr_size + 3 * mm, y + 16 * mm, "Verifique autenticidade em:")
        c.drawString(MARGIN + qr_size + 3 * mm, y + 12 * mm, url)
        emitente = empresa.designacao if empresa else ""
        nuit_emit = empresa.nuit if empresa else ""
        c.drawString(MARGIN + qr_size + 3 * mm, y + 8 * mm, f"Emitido por: {emitente}")
        c.drawString(MARGIN + qr_size + 3 * mm, y + 4 * mm, f"NUIT: {nuit_emit}")

    _draw_linha(c, MARGIN, y - 1 * mm, PAGE_W - MARGIN, color=BORDER, w=0.5)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 7.5)
    cert = empresa.numero_certificacao if empresa and empresa.numero_certificacao else "[Nº de certificacao]"
    c.drawString(MARGIN, y - 5 * mm, f"Processado por computador · SGE - FATURACAO · {cert}")
    c.drawRightString(PAGE_W - MARGIN, y - 5 * mm, f"Pagina 1 de 1 ({via})")


def gerar_pdf_documento(doc: Documento, empresa: Empresa | None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"{doc.numero_formatado or 'Rascunho'}")
    c.setAuthor((empresa.designacao if empresa else "Genesis"))
    
    tipo_str = doc.tipo_documento.value if hasattr(doc.tipo_documento, 'value') else str(doc.tipo_documento)
    c.setSubject(tipo_str)

    if tipo_str == "RC":
        _desenhar_recibo(c, doc, empresa, "ORIGINAL")
        c.showPage()
        _desenhar_recibo(c, doc, empresa, "DUPLICADO")
    else:
        _desenhar_pagina(c, doc, empresa, "ORIGINAL")
        c.showPage()
        _desenhar_pagina(c, doc, empresa, "DUPLICADO")
        
    c.showPage()
    c.save()
    return buf.getvalue()