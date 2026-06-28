"""
PDF generation — sales invoices and report exports using ReportLab Platypus.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

INDIGO = colors.HexColor("#1B2A4A")
AMBER = colors.HexColor("#D98E3F")
CHARCOAL = colors.HexColor("#3D3D38")
LIGHT_BG = colors.HexColor("#F6F1E7")


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="InvoiceTitle", fontSize=22, leading=26, textColor=INDIGO, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle(name="CompanyName", fontSize=13, leading=16, textColor=INDIGO, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle(name="SmallMuted", fontSize=9, leading=12, textColor=CHARCOAL))
    base.add(ParagraphStyle(name="SectionLabel", fontSize=9, leading=12, textColor=AMBER, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle(name="RightAlign", fontSize=10, alignment=TA_RIGHT, textColor=CHARCOAL))
    base.add(ParagraphStyle(name="TotalLabel", fontSize=11, alignment=TA_RIGHT, fontName="Helvetica-Bold", textColor=INDIGO))
    return base


def generate_invoice_pdf(order):
    """order: SalesOrder model instance. Returns BytesIO buffer of the PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=24*mm, bottomMargin=24*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    styles = _styles()
    story = []

    # Header: company + invoice meta
    header_table = Table([
        [Paragraph("SmartTex Inventory", styles["CompanyName"]),
         Paragraph(f"<b>INVOICE</b>", styles["InvoiceTitle"])],
        [Paragraph("Textile &amp; Production Management", styles["SmallMuted"]),
         Paragraph(f"#{order.invoice_number}", styles["RightAlign"])],
    ], colWidths=[100*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=AMBER, thickness=2))
    story.append(Spacer(1, 14))

    # Bill-to / order info
    customer = order.customer
    bill_to = [
        Paragraph("BILL TO", styles["SectionLabel"]),
        Paragraph(f"<b>{customer.name}</b>", styles["Normal"]),
    ]
    if customer.company_name:
        bill_to.append(Paragraph(customer.company_name, styles["SmallMuted"]))
    if customer.phone:
        bill_to.append(Paragraph(customer.phone, styles["SmallMuted"]))
    if customer.email:
        bill_to.append(Paragraph(customer.email, styles["SmallMuted"]))
    if customer.address:
        bill_to.append(Paragraph(customer.address, styles["SmallMuted"]))

    order_info = [
        Paragraph("INVOICE DETAILS", styles["SectionLabel"]),
        Paragraph(f"Date: {order.order_date.strftime('%d %b %Y') if order.order_date else '—'}", styles["SmallMuted"]),
        Paragraph(f"Payment Status: <b>{order.payment_status}</b>", styles["SmallMuted"]),
    ]
    if order.created_by:
        order_info.append(Paragraph(f"Issued by: {order.created_by.full_name}", styles["SmallMuted"]))

    info_table = Table([[bill_to, order_info]], colWidths=[100*mm, 70*mm])
    info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Line items
    rows = [["#", "Fabric", "Quantity (m)", "Unit Price", "Subtotal"]]
    for i, item in enumerate(order.items, start=1):
        rows.append([
            str(i),
            item.fabric.name if item.fabric else "—",
            f"{item.quantity_meters:.1f}",
            f"Rs. {item.unit_price:,.2f}",
            f"Rs. {item.subtotal:,.2f}",
        ])

    items_table = Table(rows, colWidths=[10*mm, 70*mm, 30*mm, 30*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#D8D5C9")),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 16))

    # Totals
    totals_rows = [
        ["Subtotal", f"Rs. {order.subtotal:,.2f}"],
        [f"Tax ({order.tax_percent or 0:.1f}%)", f"Rs. {order.tax_amount:,.2f}"],
    ]
    if order.discount_amount:
        totals_rows.append(["Discount", f"- Rs. {order.discount_amount:,.2f}"])
    totals_rows.append(["TOTAL", f"Rs. {order.total_amount:,.2f}"])
    totals_rows.append(["Amount Paid", f"Rs. {order.amount_paid:,.2f}"])
    totals_rows.append(["Balance Due", f"Rs. {order.balance_due:,.2f}"])

    totals_table = Table(totals_rows, colWidths=[40*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, -3), (-1, -3), "Helvetica-Bold"),
        ("FONTSIZE", (0, -3), (-1, -3), 12),
        ("TEXTCOLOR", (0, -3), (-1, -3), INDIGO),
        ("LINEABOVE", (0, -3), (-1, -3), 1, AMBER),
        ("TOPPADDING", (0, -3), (-1, -3), 8),
    ]))
    wrapper = Table([[None, totals_table]], colWidths=[100*mm, 80*mm])
    story.append(wrapper)

    if order.notes:
        story.append(Spacer(1, 20))
        story.append(Paragraph("NOTES", styles["SectionLabel"]))
        story.append(Paragraph(order.notes, styles["SmallMuted"]))

    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D8D5C9"), thickness=1))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Generated by SmartTex Inventory · Thank you for your business.",
        ParagraphStyle(name="Footer", fontSize=8.5, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf


def generate_table_report_pdf(title, subtitle, headers, rows):
    """Generic tabular report PDF (inventory, suppliers, sales, etc.)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=18*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    styles = _styles()
    story = []

    story.append(Paragraph("SmartTex Inventory", styles["CompanyName"]))
    story.append(Paragraph(title, styles["InvoiceTitle"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["SmallMuted"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=AMBER, thickness=2))
    story.append(Spacer(1, 16))

    data = [headers] + [[str(c) for c in row] for row in rows]
    col_count = len(headers)
    avail_width = 180 * mm
    col_width = avail_width / col_count
    table = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    story.append(table)

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Generated by SmartTex Inventory on {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}",
        ParagraphStyle(name="Footer2", fontSize=8.5, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf
