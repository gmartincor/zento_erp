from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from io import BytesIO


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    
    story.append(Paragraph(f"FACTURA {invoice.reference}", title_style))
    story.append(Spacer(1, 20))
    
    company_data = [
        ['Emisor:', 'Enviar a:'],
        [f"{invoice.company.business_name} {invoice.company.tax_id}", f"{invoice.client_name}"],
        [f"{invoice.company.legal_name}" if invoice.company.legal_name else "", f"{invoice.client_tax_id}" if invoice.client_tax_id else ""],
        [f"{invoice.company.address}", f"{invoice.client_address}"],
        [f"{invoice.company.city} {invoice.company.postal_code}", ""],
    ]
    
    company_table = Table(company_data, colWidths=[8*cm, 8*cm])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(company_table)
    story.append(Spacer(1, 20))
    
    lines_data = [['Descripción', 'Cant.', 'Precio', 'IVA', 'Total']]
    for line in invoice.lines.all():
        lines_data.append([
            line.description,
            str(line.quantity),
            f"{line.unit_price:.2f} €",
            f"{line.vat_rate:.0f}%",
            f"{line.line_total:.2f} €"
        ])
    
    lines_table = Table(lines_data, colWidths=[8*cm, 2*cm, 2*cm, 2*cm, 2*cm])
    lines_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(lines_table)
    story.append(Spacer(1, 20))
    
    totals_data = [
        ['Total (Base imp).', f"{invoice.subtotal:.2f} €"],
        [f'Total IVA', f"{invoice.vat_amount:.2f} €"],
    ]
    
    if invoice.irpf_amount > 0:
        totals_data.append([f'Total IRPF -{invoice.company.irpf_rate:.0f}%', f"-{invoice.irpf_amount:.2f} €"])
    
    totals_data.append(['TOTAL', f"{invoice.total_amount:.2f} €"])
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 20))
    
    payment_info = f"""
    Condiciones de pago: {invoice.payment_terms}
    Banco: {invoice.company.bank_name}
    IBAN: {invoice.company.iban}
    """
    
    story.append(Paragraph(payment_info, styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
