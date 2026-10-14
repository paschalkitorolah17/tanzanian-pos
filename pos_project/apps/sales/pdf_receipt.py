"""
Generate a thermal-style PDF receipt using ReportLab.
"""

from io import BytesIO
from decimal import Decimal

from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as MM
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_receipt_pdf(sale) -> BytesIO:
    """
    Create a simple 80mm-wide PDF receipt and return it as BytesIO.
    """
    width = 80 * MM
    # Dynamic height based on number of items
    base_height = 120 * MM
    item_height = 6 * MM
    height = base_height + (sale.items.count() * item_height)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))

    y = height - 10 * MM
    left = 5 * MM
    right = width - 5 * MM
    center = width / 2

    def text(txt, x, y, size=9, bold=False, align='left'):
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        if align == 'center':
            c.drawCentredString(x, y, str(txt))
        elif align == 'right':
            c.drawRightString(x, y, str(txt))
        else:
            c.drawString(x, y, str(txt))

    def line(y):
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setDash(1, 2)
        c.line(left, y, right, y)
        c.setDash()

    business = sale.business

    # Header
    text(business.name, center, y, size=11, bold=True, align='center')
    y -= 5 * MM

    if business.address:
        text(business.address[:40], center, y, size=8, align='center')
        y -= 4 * MM
    if business.phone:
        text(f'Tel: {business.phone}', center, y, size=8, align='center')
        y -= 4 * MM
    if getattr(business, 'tin', None):
        text(f'TIN: {business.tin}', center, y, size=8, align='center')
        y -= 4 * MM

    y -= 2 * MM
    line(y)
    y -= 5 * MM

    # Meta
    text(f'Receipt: {sale.transaction_number}', left, y, size=8, bold=True)
    y -= 4 * MM
    text(f'Date: {sale.created_at.strftime("%d/%m/%Y %H:%M")}', left, y, size=8)
    y -= 4 * MM
    text(f'Cashier: {sale.cashier.get_full_name() or sale.cashier.username}', left, y, size=8)
    y -= 4 * MM
    text(f'Branch: {sale.branch.name}', left, y, size=8)
    y -= 4 * MM
    if sale.customer:
        text(f'Customer: {sale.customer.name}', left, y, size=8)
        y -= 4 * MM

    y -= 2 * MM
    line(y)
    y -= 5 * MM

    # Items header
    text('Item', left, y, size=8, bold=True)
    text('Qty', left + 42 * MM, y, size=8, bold=True)
    text('Total', right, y, size=8, bold=True, align='right')
    y -= 4 * MM

    for item in sale.items.all():
        name = item.product.name[:22]
        text(name, left, y, size=8)
        text(str(int(item.quantity)), left + 42 * MM, y, size=8)
        text(f'{item.line_total:.0f}', right, y, size=8, align='right')
        y -= 4 * MM
        if item.discount and item.discount > 0:
            text(f'  Disc: -{item.discount:.0f}', left, y, size=7)
            y -= 3.5 * MM

    y -= 2 * MM
    line(y)
    y -= 5 * MM

    # Totals
    text('Subtotal', left, y, size=8)
    text(f'{sale.subtotal:.0f}', right, y, size=8, align='right')
    y -= 4 * MM

    if sale.discount_total and sale.discount_total > 0:
        text('Discount', left, y, size=8)
        text(f'-{sale.discount_total:.0f}', right, y, size=8, align='right')
        y -= 4 * MM

    if sale.tax_total and sale.tax_total > 0:
        text('Tax (VAT)', left, y, size=8)
        text(f'{sale.tax_total:.0f}', right, y, size=8, align='right')
        y -= 4 * MM

    text('TOTAL', left, y, size=10, bold=True)
    text(f'TZS {sale.grand_total:.0f}', right, y, size=10, bold=True, align='right')
    y -= 6 * MM

    line(y)
    y -= 5 * MM

    # Payments
    text('Payments', left, y, size=8, bold=True)
    y -= 4 * MM
    for p in sale.payments.all():
        label = p.payment_method.name
        if p.reference:
            label += f' ({p.reference})'
        text(label[:28], left, y, size=8)
        text(f'{p.amount:.0f}', right, y, size=8, align='right')
        y -= 4 * MM

    y -= 3 * MM
    line(y)
    y -= 6 * MM

    # Footer
    footer = getattr(business, 'receipt_footer', None) or 'Asante kwa kununua!\nKaribu tena.'
    for line_txt in footer.split('\n'):
        text(line_txt.strip(), center, y, size=8, align='center')
        y -= 4 * MM

    y -= 3 * MM
    text('Powered by Tanzanian POS', center, y, size=7, align='center')

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
