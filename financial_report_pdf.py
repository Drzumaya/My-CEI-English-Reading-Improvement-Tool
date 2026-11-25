from datetime import datetime
import hashlib
import io
import os
from fpdf import FPDF


def _txt_pdf(val: str) -> str:
    """Normaliza caracteres UTF-8 a Latin-1 seguro para FPDF."""
    s = str(val or "").replace("—", "-").replace("–", "-").replace("•", "*")
    return s.encode("latin-1", errors="replace").decode("latin-1")


class CEIExecutiveFinancialPDF(FPDF):
    def __init__(self, campus_info: dict, periodo_label: str, folio_doc: str):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.campus_info = campus_info
        self.periodo_label = periodo_label
        self.folio_doc = folio_doc
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        # Banda superior azul marino institucional (#0B2545)
        self.set_fill_color(11, 37, 69)
        self.rect(0, 0, 216, 28, "F")

        # Logo oficial si existe
        for logo_p in ["static/LOGO CEI APP.png", "LOGO CEI APP.png"]:
            if os.path.exists(logo_p):
                self.image(logo_p, x=12, y=4, w=20)
                break

        self.set_xy(36, 6)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.cell(115, 6, _txt_pdf("CAREER ENGLISH INSTITUTE (CEI)"), ln=1)

        self.set_x(36)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(203, 213, 225)
        sede_txt = f"{self.campus_info.get('nombre_plantel', 'Sede Central')} ({self.campus_info.get('campus_id', 'CEI-HQ')})"
        self.cell(115, 4.5, _txt_pdf(f"ESTADO FINANCIERO EJECUTIVO (NIF / IFRS) | {sede_txt}"), ln=1)

        # Metadatos derecha
        self.set_xy(152, 6)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(250, 204, 21)
        self.cell(52, 5, _txt_pdf(f"FOLIO: {self.folio_doc}"), align="R", ln=1)

        self.set_x(152)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(255, 255, 255)
        self.cell(52, 4.5, _txt_pdf(f"Periodo: {self.periodo_label}"), align="R", ln=1)

        self.set_x(152)
        self.cell(52, 4.5, _txt_pdf(f"Moneda: {self.campus_info.get('moneda', 'MXN')}"), align="R", ln=1)
        self.ln(8)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(203, 213, 225)
        self.line(12, self.get_y(), 204, self.get_y())
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 116, 139)
        dir_inst = self.campus_info.get("direccion_oficial", "Agua Prieta, Sonora, Mexico")
        self.cell(140, 6, _txt_pdf(f"CEI • {dir_inst} | Documento Confidencial de Alta Gerencia"), align="L")
        self.cell(52, 6, _txt_pdf(f"Pagina {self.page_no()}/{{nb}}"), align="R")


def generar_pdf_estado_financiero_gerencial(
    campus_info: dict,
    periodo_label: str,
    resumen_kpis: dict,
    lineas_pnl: list[dict],
    detalle_conceptos: list[dict],
    emisor_nombre: str = "Jacob Zumaya Prianti"
) -> tuple[bytes, str]:
    """
    Genera el PDF Ejecutivo de Estado Financiero bajo formato Board Pack (NIF/IFRS).
    Devuelve (pdf_bytes, folio_generado).
    """
    ts_now = datetime.now().strftime("%Y%m%d-%H%M")
    folio_doc = f"FIN-CEI-{ts_now}"
    pdf = CEIExecutiveFinancialPDF(campus_info, periodo_label, folio_doc)
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. TARJETAS DE KPIs EJECUTIVOS (4 COLUMNAS)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 6, _txt_pdf("1. RESUMEN EJECUTIVO DE DESEMPENO FINANCIERO"), ln=1)
    pdf.ln(1)

    kpis_cards = [
        ("INGRESOS BRUTOS", f"${resumen_kpis.get('ingresos_brutos', 0.0):,.2f}", (240, 249, 255), (3, 105, 161)),
        ("IVA TRASLADADO", f"${resumen_kpis.get('iva_total', 0.0):,.2f}", (248, 250, 252), (51, 65, 85)),
        ("COMISIONES Y EGRESOS", f"${resumen_kpis.get('egresos_totales', 0.0):,.2f}", (254, 242, 242), (185, 28, 28)),
        ("UTILIDAD NETA", f"${resumen_kpis.get('utilidad_neta', 0.0):,.2f}", (240, 253, 244), (21, 128, 61)),
    ]
    start_x = 12
    y_cards = pdf.get_y()
    card_w = 45.5
    gap = 2.6
    for idx, (lbl, val_str, bg_rgb, txt_rgb) in enumerate(kpis_cards):
        cx = start_x + idx * (card_w + gap)
        pdf.set_fill_color(*bg_rgb)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(cx, y_cards, card_w, 18, "FD")
        pdf.set_xy(cx + 2, y_cards + 2.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 4, 4, _txt_pdf(lbl), ln=1)
        pdf.set_x(cx + 2)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*txt_rgb)
        pdf.cell(card_w - 4, 7, _txt_pdf(val_str), ln=1)

    pdf.set_y(y_cards + 23)

    # 2. ESTADO DE RESULTADOS CONSOLIDADO (P&L)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 6, _txt_pdf("2. ESTADO DE RESULTADOS CONSOLIDADO (P&L)"), ln=1)

    # Encabezado de tabla
    pdf.set_fill_color(11, 37, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(112, 7, _txt_pdf("  CONCEPTO CONTABLE"), border=1, fill=True)
    pdf.cell(44, 7, _txt_pdf("IMPORTE"), border=1, align="R", fill=True)
    pdf.cell(36, 7, _txt_pdf("% S/ INGRESO  "), border=1, align="R", fill=True, ln=1)

    for item in lineas_pnl:
        es_total = bool(item.get("es_total", False))
        pdf.set_fill_color(241, 245, 249) if es_total else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B" if es_total else "", 8.5)
        pdf.cell(112, 6.5, _txt_pdf(f"  {item.get('concepto', '')}"), border=1, fill=True)
        pdf.cell(44, 6.5, _txt_pdf(f"${float(item.get('monto', 0.0)):,.2f}"), border=1, align="R", fill=True)
        pdf.cell(36, 6.5, _txt_pdf(f"{float(item.get('pct', 0.0)):.1f}%  "), border=1, align="R", fill=True, ln=1)

    pdf.ln(5)

    # 3. DESGLOSE ANALÍTICO POR RUBRO / BLOQUE / AFILIADOS
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 6, _txt_pdf("3. DESGLOSE OPERATIVO Y CARTERA POR RUBRO"), ln=1)

    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(82, 6.5, _txt_pdf("  RUBRO / CATEGORIA"), border=1, fill=True)
    pdf.cell(28, 6.5, _txt_pdf("MOVIMIENTOS"), border=1, align="C", fill=True)
    pdf.cell(42, 6.5, _txt_pdf("SUBTOTAL"), border=1, align="R", fill=True)
    pdf.cell(40, 6.5, _txt_pdf("TOTAL C/ IVA  "), border=1, align="R", fill=True, ln=1)

    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "", 8)
    for det in detalle_conceptos:
        pdf.cell(82, 6, _txt_pdf(f"  {det.get('rubro', '')}"), border=1)
        pdf.cell(28, 6, _txt_pdf(str(det.get("movimientos", 0))), border=1, align="C")
        pdf.cell(42, 6, _txt_pdf(f"${float(det.get('subtotal', 0.0)):,.2f}"), border=1, align="R")
        pdf.cell(40, 6, _txt_pdf(f"${float(det.get('total', 0.0)):,.2f}  "), border=1, align="R", ln=1)

    pdf.ln(8)

    # 4. SELLO CRIPTOGRÁFICO DE AUDITORÍA Y FIRMAS DE ALTA GERENCIA
    raw_hash = f"{folio_doc}|{periodo_label}|{resumen_kpis.get('utilidad_neta', 0.0)}|{emisor_nombre}"
    sha_code = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()[:32].upper()

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(148, 163, 184)
    y_seal = pdf.get_y()
    pdf.rect(12, y_seal, 192, 14, "FD")
    pdf.set_xy(15, y_seal + 2)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 4, _txt_pdf(f"SELLO DIGITAL DE INTEGRIDAD CONTABLE (SHA-256): {sha_code}"), ln=1)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 4, _txt_pdf(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Autorizado por: {emisor_nombre}"), ln=1)

    pdf.set_y(y_seal + 24)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(90, 5, "________________________________________", align="C")
    pdf.cell(12, 5, "")
    pdf.cell(90, 5, "________________________________________", align="C", ln=1)

    pdf.cell(90, 5, _txt_pdf(emisor_nombre), align="C")
    pdf.cell(12, 5, "")
    pdf.cell(90, 5, _txt_pdf("Contraloria y Administracion Financiera"), align="C", ln=1)

    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(90, 4, _txt_pdf("Direccion General — Career English Institute"), align="C")
    pdf.cell(12, 4, "")
    pdf.cell(90, 4, _txt_pdf("Validacion Interna y Fiscal"), align="C", ln=1)

    pdf_out = pdf.output(dest="S")
    pdf_bytes = bytes(pdf_out) if isinstance(pdf_out, (bytes, bytearray)) else pdf_out.encode("latin-1")
    return pdf_bytes, folio_doc
