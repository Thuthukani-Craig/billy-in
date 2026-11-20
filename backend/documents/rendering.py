from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.core.files.storage import default_storage
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


THEMES = {
    "CLASSIC": {"accent": "#1F2937", "muted": "#64748B", "rule": "#CBD5E1"},
    "MODERN": {"accent": "#2563EB", "muted": "#475569", "rule": "#BFDBFE"},
    "MINIMAL": {"accent": "#111827", "muted": "#6B7280", "rule": "#E5E7EB"},
    "CORPORATE": {"accent": "#123B5D", "muted": "#526579", "rule": "#CBD5E1"},
    "BOLD": {"accent": "#B45309", "muted": "#57534E", "rule": "#FCD34D"},
    "INDUSTRIAL": {"accent": "#374151", "muted": "#6B7280", "rule": "#9CA3AF"},
}


def _p(value, style):
    return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), style)


def render_document_pdf(document):
    snapshot = document.issued_snapshot
    if not snapshot:
        raise ValueError("This document has no issued snapshot and cannot be rendered as an official PDF.")

    presentation = snapshot.get("presentation", {})
    theme = THEMES.get(presentation.get("theme", "CLASSIC"), THEMES["CLASSIC"])
    accent = colors.HexColor(presentation.get("primary_colour") or theme["accent"])
    muted = colors.HexColor(theme["muted"])
    rule = colors.HexColor(theme["rule"])
    data = snapshot["document"]
    business = snapshot["business"]
    customer = snapshot["customer"]
    totals = snapshot["totals"]

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title=f'{data["type"]} {data["number"]}',
        author=business.get("name", "Billy-in"),
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle("DocTitle", parent=base["Title"], fontName="Helvetica-Bold",
                           fontSize=23, leading=27, textColor=accent, alignment=TA_RIGHT, spaceAfter=4)
    heading = ParagraphStyle("SectionHeading", parent=base["Heading3"], fontSize=9,
                             leading=12, textColor=muted, spaceAfter=4)
    body = ParagraphStyle("BodySmall", parent=base["BodyText"], fontSize=8.5, leading=12)
    right = ParagraphStyle("RightSmall", parent=body, alignment=TA_RIGHT)
    small = ParagraphStyle("SmallMuted", parent=body, textColor=muted, fontSize=7.5)
    story = []

    logo_name = business.get("logo_storage_name")
    if presentation.get("show_logo", True) and logo_name and default_storage.exists(logo_name):
        try:
            with default_storage.open(logo_name, "rb") as logo_file:
                logo_bytes = BytesIO(logo_file.read())
            logo = Image(logo_bytes, width=34 * mm, height=18 * mm, kind="proportional")
        except Exception:
            logo = _p(business.get("trading_name") or business.get("name"), heading)
    else:
        logo = _p(business.get("trading_name") or business.get("name"), heading)

    business_lines = [
        business.get("name"),
        business.get("registration_number") if presentation.get("show_business_registration", True) else "",
        business.get("vat_registration_number") if presentation.get("show_business_registration", True) else "",
        business.get("physical_address"),
        business.get("email"), business.get("telephone"),
    ]
    business_block = [_p(line, body) for line in business_lines if line]
    header = Table([[logo, [_p(data["type"].replace("_", " "), title),
                             _p(data["number"], right),
                             _p(f'Issued: {data.get("issue_date") or "—"}', right),
                             _p(f'Due: {data.get("due_date") or "—"}', right)]]],
                   colWidths=[90 * mm, 84 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, accent),
    ]))
    story.extend([header, Spacer(1, 7 * mm)])
    story.extend(business_block)
    story.append(Spacer(1, 5 * mm))

    customer_lines = [customer.get("name"), customer.get("contact_person"),
                      customer.get("billing_address") or customer.get("physical_address"),
                      customer.get("email"), customer.get("telephone"),
                      customer.get("vat_number") if presentation.get("show_customer_vat_number", True) else ""]
    customer_block = [_p(line, body) for line in customer_lines if line]
    party_table = Table([[[_p("BILLED TO", heading)] + customer_block,
                          [_p("FROM", heading)] + business_block]],
                        colWidths=[87 * mm, 87 * mm])
    party_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, rule),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([party_table, Spacer(1, 8 * mm)])

    rows = [[_p("DESCRIPTION", heading), _p("QTY", right), _p("UNIT PRICE", right),
             _p("DISCOUNT", right), _p("TAX", right), _p("TOTAL", right)]]
    for item in snapshot.get("line_items", []):
        qty = item.get("quantity", "0")
        unit = item.get("unit_of_measure", "")
        rows.append([
            _p(item.get("description"), body),
            _p(f'{qty} {unit}'.strip(), right),
            _p(f'R {Decimal(item["unit_price"]):,.2f}', right),
            _p(f'R {Decimal(item["discount"]):,.2f}', right),
            _p(f'{item["tax_rate"]}%', right),
            _p(f'R {Decimal(item["line_total"]):,.2f}', right),
        ])
    items_table = Table(rows, colWidths=[67 * mm, 20 * mm, 25 * mm, 22 * mm, 15 * mm, 25 * mm], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, rule),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([items_table, Spacer(1, 6 * mm)])

    summary_rows = [
        [_p("Subtotal", body), _p(f'R {Decimal(totals["subtotal"]):,.2f}', right)],
        [_p("Discount", body), _p(f'- R {Decimal(totals["discount_amount"]):,.2f}', right)],
        [_p("Tax", body), _p(f'R {Decimal(totals["tax_amount"]):,.2f}', right)],
        [_p("TOTAL", heading), _p(f'R {Decimal(totals["total"]):,.2f}', right)],
        [_p("Paid", body), _p(f'R {Decimal(totals["amount_paid"]):,.2f}', right)],
        [_p("Balance due", heading), _p(f'R {Decimal(totals["outstanding_balance"]):,.2f}', right)],
    ]
    summary = Table(summary_rows, colWidths=[42 * mm, 38 * mm], hAlign="RIGHT")
    summary.setStyle(TableStyle([
        ("LINEABOVE", (0, 3), (-1, 3), 1.2, accent),
        ("LINEBELOW", (0, 3), (-1, 3), 1.2, accent),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary)

    payment_lines = [
        ("Bank", business.get("banking_institution")),
        ("Account holder", business.get("account_holder")),
        ("Account number", business.get("account_number")),
        ("Branch code", business.get("branch_code")),
        ("Account type", business.get("account_type")),
    ]
    payment_lines = [f"{label}: {value}" for label, value in payment_lines if value]
    if presentation.get("show_payment_details", True) and (payment_lines or business.get("payment_instructions")):
        story.extend([Spacer(1, 8 * mm), _p("PAYMENT DETAILS", heading)])
        story.extend([_p(line, body) for line in payment_lines])
        if business.get("payment_instructions"):
            story.append(_p(business["payment_instructions"], body))
    if data.get("notes"):
        story.extend([Spacer(1, 6 * mm), _p("NOTES", heading), _p(data["notes"], body)])
    if business.get("invoice_footer"):
        story.extend([Spacer(1, 8 * mm), _p(business["invoice_footer"], small)])
    story.extend([Spacer(1, 8 * mm), _p("Generated by Billy-in • Please retain this document for your records.", small)])

    pdf.build(story)
    return buffer.getvalue()
