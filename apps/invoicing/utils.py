from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
import os


def get_pdf_styles():
    styles = getSampleStyleSheet()
    return {
        'company': ParagraphStyle('Company', parent=styles['Normal'], fontSize=10, spaceBefore=0, spaceAfter=0),
        'invoice_title': ParagraphStyle('InvoiceTitle', parent=styles['Normal'], fontSize=16, alignment=TA_RIGHT, fontName='Helvetica-Bold'),
        'invoice_data': ParagraphStyle('InvoiceData', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT),
        'section_title': ParagraphStyle('SectionTitle', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4),
        'client': ParagraphStyle('Client', parent=styles['Normal'], fontSize=9),
        'table_content': ParagraphStyle('TableContent', parent=styles['Normal'], fontSize=9),
        'legal': ParagraphStyle('Legal', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
        'footer': ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
    }


def create_professional_header(invoice, styles):
    company_info = [f"<b>{invoice.company.business_name}</b>"]
    
    if invoice.company.legal_name and invoice.company.legal_name != invoice.company.business_name:
        company_info.append(invoice.company.legal_name)
    
    company_info.extend([
        f"NIF/CIF: {invoice.company.tax_id}",
        f"Régimen empresarial: {invoice.company.get_legal_form_display()}" if invoice.company.legal_form else "Régimen empresarial: Empresario Individual",
        f"Dirección: {invoice.company.get_full_address()}"
    ])
    
    if invoice.company.phone:
        company_info.append(f"Tel: {invoice.company.phone}")
    if invoice.company.email:
        company_info.append(f"Email: {invoice.company.email}")
    
    invoice_info = [
        f"<b>FACTURA {invoice.reference}</b>",
        f"Fecha: {invoice.issue_date.strftime('%d/%m/%Y')}"
    ]
    
    if hasattr(invoice, 'due_date') and invoice.due_date:
        invoice_info.append(f"Vencimiento: {invoice.due_date.strftime('%d/%m/%Y')}")
    
    left_content = company_info
    if invoice.company.logo and os.path.exists(invoice.company.logo.path):
        left_content.insert(0, f'<img src="{invoice.company.logo.path}" width="60" height="30" valign="top"/>')
    
    header_data = [[
        Paragraph("<br/>".join(left_content), styles['company']),
        Paragraph("<br/>".join(invoice_info), styles['invoice_data'])
    ]]
    
    header_table = Table(header_data, colWidths=[11*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    return header_table


def create_client_section(invoice, styles):
    client_info = [
        f"<b>FACTURAR A:</b>",
        f"{invoice.client_name}",
        f"Régimen empresarial: {invoice.get_client_type_display()}",
        f"Dirección: {invoice.client_address}"
    ]
    
    if invoice.client_tax_id:
        client_info.append(f"NIF/CIF: {invoice.client_tax_id}")
    
    client_data = [[Paragraph("<br/>".join(client_info), styles['client'])]]
    
    client_table = Table(client_data, colWidths=[17*cm])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    return client_table


def format_percentage(rate):
    if not rate:
        return "0%"
    percentage = rate if rate >= 1 else rate * 100
    return f"{percentage:.0f}%"


def create_services_section(invoice, styles):
    headers = ['Descripción', 'Cant.', 'Precio Unit.', 'IVA', 'IRPF', 'Total']
    service_data = [headers]
    
    for item in invoice.items.all():
        service_data.append([
            Paragraph(item.description.replace('\n', '<br/>'), styles['table_content']),
            str(item.quantity),
            format_currency(item.unit_price),
            format_percentage(item.vat_rate),
            format_percentage(item.irpf_rate),
            format_currency(item.line_total)
        ])
    
    service_table = Table(service_data, colWidths=[7*cm, 1*cm, 2*cm, 1.5*cm, 1.5*cm, 2*cm])
    service_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    
    return service_table


def create_totals_section(invoice, styles):
    payment_info = []
    if invoice.payment_terms:
        payment_info.extend([
            f"<b>FORMA DE PAGO</b>",
            f"Condiciones: {invoice.payment_terms}",
            ""
        ])
    
    if invoice.company.bank_name and invoice.company.iban:
        payment_info.extend([
            "<b>Datos bancarios:</b>",
            f"Banco: {invoice.company.bank_name}",
            f"IBAN: {invoice.company.iban}"
        ])
    
    totals_data = [
        ["Subtotal (Base imponible)", format_currency(invoice.base_amount)]
    ]
    
    if invoice.vat_amount > 0:
        vat_rate = invoice.items.first().vat_rate if invoice.items.exists() else 0
        totals_data.append([f"IVA ({format_percentage(vat_rate)})", format_currency(invoice.vat_amount)])
    
    if invoice.irpf_amount > 0:
        irpf_rate = invoice.items.first().irpf_rate if invoice.items.exists() else 0
        totals_data.append([f"Retención IRPF ({format_percentage(irpf_rate)})", f"-{format_currency(invoice.irpf_amount)}"])
    
    totals_data.append(["TOTAL A PAGAR", format_currency(invoice.total_amount)])
    
    totals_table = Table(totals_data, colWidths=[4*cm, 2.5*cm])
    totals_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    final_data = [[
        Paragraph("<br/>".join(payment_info), styles['table_content']),
        totals_table
    ]]
    
    final_table = Table(final_data, colWidths=[10.5*cm, 6.5*cm])
    final_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    return final_table


def format_currency(amount):
    return f"{amount:.2f} €"


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=20*mm, 
        leftMargin=20*mm, 
        topMargin=20*mm, 
        bottomMargin=30*mm
    )
    
    styles = get_pdf_styles()
    story = []
    
    story.append(create_professional_header(invoice, styles))
    story.append(Spacer(1, 12*mm))
    
    story.append(create_client_section(invoice, styles))
    story.append(Spacer(1, 8*mm))
    
    story.append(create_services_section(invoice, styles))
    story.append(Spacer(1, 8*mm))
    
    story.append(create_totals_section(invoice, styles))
    story.append(Spacer(1, 10*mm))
    
    legal_note = invoice.get_legal_note()
    if legal_note:
        story.append(Paragraph(legal_note, styles['legal']))
        story.append(Spacer(1, 5*mm))
    
    legal_info = []
    optional_info = []
    
    if invoice.company.mercantile_registry:
        optional_info.append(f"Registro Mercantil: {invoice.company.mercantile_registry}")
    if invoice.company.share_capital:
        optional_info.append(f"Capital Social: {invoice.company.share_capital:.2f} €")
    
    if invoice.irpf_amount > 0:
        legal_info.append("Factura sujeta a retención de IRPF según normativa fiscal vigente")
    if invoice.vat_amount > 0:
        legal_info.append("IVA incluido según legislación vigente")
    
    legal_info.append("Factura emitida según Real Decreto 1619/2012 sobre obligaciones de facturación")
    
    if optional_info:
        story.append(Paragraph(" | ".join(optional_info), styles['legal']))
        story.append(Spacer(1, 3*mm))
    
    if legal_info:
        story.append(Paragraph(" | ".join(legal_info), styles['legal']))
        story.append(Spacer(1, 5*mm))
    
    entity_display = "Empresario Individual" if invoice.company.is_freelancer else invoice.company.get_legal_form_display()
    story.append(Paragraph(f"{entity_display} - Página 1", styles['footer']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
