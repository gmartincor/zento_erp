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
        'header': ParagraphStyle(
            'Header', parent=styles['Normal'], fontSize=10, spaceAfter=6
        ),
        'title': ParagraphStyle(
            'Title', parent=styles['Normal'], fontSize=14, 
            alignment=TA_RIGHT, spaceBefore=0, spaceAfter=12
        ),
        'section': ParagraphStyle(
            'Section', parent=styles['Normal'], fontSize=9, 
            spaceBefore=6, spaceAfter=6
        ),
        'note': ParagraphStyle(
            'Note', parent=styles['Normal'], fontSize=8, 
            alignment=TA_CENTER, spaceBefore=3, spaceAfter=8
        ),
        'footer': ParagraphStyle(
            'Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER
        )
    }


def create_header_table(invoice, styles):
    left_header = []
    if invoice.company.logo and os.path.exists(invoice.company.logo.path):
        left_header.append(f'<img src="{invoice.company.logo.path}" width="80" height="40"/>')
    
    left_header.extend([
        f"<b>{invoice.company.business_name}</b>",
        f"{invoice.company.legal_name or ''}" if invoice.company.legal_name and invoice.company.legal_name != invoice.company.business_name else "",
        f"NIF/CIF: {invoice.company.tax_id}",
        f"{invoice.company.get_legal_form_display()}" if invoice.company.legal_form else "",
        invoice.company.get_full_address()
    ])
    
    right_header = [
        f"<b>FACTURA {invoice.reference}</b>",
        f"Fecha: {invoice.issue_date.strftime('%d/%m/%Y')}"
    ]
    
    left_content = Paragraph("<br/>".join(filter(None, left_header)), styles['header'])
    right_content = Paragraph("<br/>".join(right_header), styles['title'])
    
    return create_two_column_table(left_content, right_content)


def create_customer_table(invoice, styles):
    emisor_text = [
        "<b>Emisor:</b>",
        f"{invoice.company.business_name}",
        f"NIF/CIF: {invoice.company.tax_id}",
    ]
    
    if invoice.company.legal_form:
        emisor_text.append(f"{invoice.company.get_legal_form_display()}")
    
    emisor_text.append(f"{invoice.company.get_full_address()}")
    
    if invoice.company.phone:
        emisor_text.append(f"Tel: {invoice.company.phone}")
    if invoice.company.email:
        emisor_text.append(f"Email: {invoice.company.email}")
    
    enviar_text = [
        "<b>Enviar a:</b>",
        f"{invoice.client_name}",
        f"{invoice.get_client_type_display()}",
        f"{invoice.client_address}"
    ]
    
    if invoice.client_tax_id:
        enviar_text.append(f"NIF/CIF: {invoice.client_tax_id}")
    
    left_content = Paragraph("<br/>".join(emisor_text), styles['section'])
    right_content = Paragraph("<br/>".join(enviar_text), styles['section'])
    
    return create_two_column_table(left_content, right_content, 8.5*cm, 8.5*cm)


def create_service_table(invoice, styles):
    service_headers = ['Descripción', 'IVA', 'IRPF', 'Cant.', 'Total (Base imp.)']
    
    description_formatted = invoice.service_description.replace('\n', '<br/>')
    irpf_display = format_rate_display(invoice.irpf_rate)
    vat_display = format_rate_display(invoice.vat_rate)
    
    service_data = [
        service_headers,
        [
            Paragraph(description_formatted, styles['section']),
            vat_display,
            irpf_display,
            str(invoice.quantity),
            format_currency(invoice.base_amount)
        ]
    ]
    
    service_table = Table(service_data, colWidths=[8*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2.5*cm])
    service_table.setStyle(get_service_table_style())
    
    return service_table


def create_payment_totals_table(invoice, styles):
    vat_display = format_rate_display(invoice.vat_rate)
    irpf_display = format_rate_display(invoice.irpf_rate)
    
    payment_info = []
    if invoice.payment_terms:
        payment_info.extend([
            f"<b>Condiciones de pago:</b> {invoice.payment_terms}",
            ""
        ])
    
    if invoice.company.bank_name and invoice.company.iban:
        payment_info.extend([
            "<b>Datos bancarios para el pago:</b>",
            f"Banco: {invoice.company.bank_name}",
            f"IBAN: {invoice.company.iban}"
        ])
    
    totals_data = [
        [f"Total (Base imp).", format_currency(invoice.base_amount)],
        [f"Total IVA {vat_display}", format_currency(invoice.vat_amount)]
    ]
    
    if invoice.irpf_amount > 0:
        totals_data.append([
            f"Retención IRPF {irpf_display}", 
            f"-{format_currency(invoice.irpf_amount)}"
        ])
    
    totals_data.append(["<b>TOTAL A PAGAR</b>", f"<b>{format_currency(invoice.total_amount)}</b>"])
    
    totals_table = Table(totals_data, colWidths=[4*cm, 2.5*cm])
    totals_table.setStyle(get_totals_table_style())
    
    left_content = Paragraph("<br/>".join(payment_info), styles['section'])
    
    return create_two_column_table(left_content, totals_table)


def format_rate_display(rate):
    """Format a rate object to display as a percentage."""
    return f"{rate.rate:.0f}%" if rate else "0%"


def format_currency(amount):
    return f"{amount:.2f} €"


def get_common_table_style():
    """Return a common TableStyle used for many tables."""
    return TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ])


def get_service_table_style():
    """Return the TableStyle used for service tables."""
    return TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ])


def get_totals_table_style():
    """Return the TableStyle used for totals tables."""
    return TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ])


def create_two_column_table(left_content, right_content, left_width=10*cm, right_width=7*cm, style=None):
    """Create a common two-column table structure."""
    table_data = [[left_content, right_content]]
    table = Table(table_data, colWidths=[left_width, right_width])
    table.setStyle(style or get_common_table_style())
    return table


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
    
    # Use the predefined styles
    styles = get_pdf_styles()
    story = []
    
    # Add header
    header_table = create_header_table(invoice, styles)
    story.append(header_table)
    story.append(Spacer(1, 15*mm))
    
    # Add customer information
    customer_table = create_customer_table(invoice, styles)
    story.append(customer_table)
    story.append(Spacer(1, 10*mm))
    
    # Add service details
    service_table = create_service_table(invoice, styles)
    story.append(service_table)
    story.append(Spacer(1, 8*mm))
    
    # Add currency note
    story.append(Paragraph("Importes visualizados en Euros", styles['note']))
    story.append(Spacer(1, 8*mm))
    
    # Add payment and totals
    final_table = create_payment_totals_table(invoice, styles)
    story.append(final_table)
    story.append(Spacer(1, 10*mm))
    
    # Add legal note if available
    legal_note = invoice.get_legal_note()
    if legal_note:
        story.append(Paragraph(legal_note, styles['note']))
        story.append(Spacer(1, 5*mm))
    
    # Add mandatory legal information
    legal_info = []
    
    # Add optional but recommended company information
    optional_info = []
    if invoice.company.mercantile_registry:
        optional_info.append(f"Registro Mercantil: {invoice.company.mercantile_registry}")
    if invoice.company.share_capital:
        optional_info.append(f"Capital Social: {invoice.company.share_capital:.2f} €")
    
    # Add tax information (mandatory)
    if invoice.irpf_amount > 0:
        legal_info.append("Factura sujeta a retención de IRPF según normativa fiscal vigente")
    if invoice.vat_amount > 0:
        legal_info.append("IVA incluido según legislación vigente")
    
    legal_info.append("Factura emitida según Real Decreto 1619/2012 sobre obligaciones de facturación")
    
    # Add optional information first if exists
    if optional_info:
        optional_text = " | ".join(optional_info)
        story.append(Paragraph(f"Información adicional: {optional_text}", styles['note']))
        story.append(Spacer(1, 3*mm))
    
    # Add mandatory legal information
    if legal_info:
        legal_text = " | ".join(legal_info)
        story.append(Paragraph(legal_text, styles['note']))
        story.append(Spacer(1, 5*mm))
    
    # Add footer
    entity_display = "Empresario Individual" if invoice.company.is_freelancer else invoice.company.get_legal_form_display()
    story.append(Paragraph(f"{entity_display} - Página 1", styles['footer']))
    
    # Build PDF and return
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
