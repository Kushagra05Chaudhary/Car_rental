"""
Invoice PDF Generator using ReportLab
"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from django.conf import settings


def generate_invoice_pdf(payment):
    """
    Generate PDF invoice for a payment
    
    Args:
        payment (Payment): Payment object
        
    Returns:
        bytes: PDF content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []
    
    booking = payment.booking
    car = booking.car
    user = payment.user
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=3,
    )
    
    # ===== HEADER =====
    story.append(Paragraph("aSk.ren", title_style))
    story.append(Paragraph("Car Rental Platform", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Invoice details
    story.append(Paragraph("INVOICE", heading_style))
    
    header_data = [
        ['Invoice ID:', f"INV-{payment.id:06d}"],
        ['Order ID:', payment.razorpay_order_id[:20]],
        ['Date:', payment.created_at.strftime('%d %b %Y')],
        ['Status:', payment.get_status_display().upper()],
    ]
    
    header_table = Table(header_data, colWidths=[2*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== CUSTOMER & BILLING INFO =====
    story.append(Paragraph("CUSTOMER DETAILS", heading_style))
    
    customer_data = [
        ['Name:', f"{user.first_name or user.username}"],
        ['Email:', user.email],
        ['Phone:', getattr(user, 'phone_number', 'N/A')],
    ]
    
    customer_table = Table(customer_data, colWidths=[1.5*inch, 3.5*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    story.append(customer_table)
    story.append(Spacer(1, 0.2*inch))
    
    # ===== VEHICLE DETAILS =====
    story.append(Paragraph("VEHICLE DETAILS", heading_style))
    
    car_data = [
        ['Car Name:', f"{car.name} ({car.brand})"],
        ['Car Type:', car.car_type],
        ['Location:', car.location],
        ['Seats:', str(car.seats)],
    ]
    
    car_table = Table(car_data, colWidths=[1.5*inch, 3.5*inch])
    car_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    story.append(car_table)
    story.append(Spacer(1, 0.2*inch))
    
    # ===== BOOKING DETAILS =====
    story.append(Paragraph("BOOKING DETAILS", heading_style))
    
    days = (booking.end_date - booking.start_date).days + 1
    
    booking_data = [
        ['Booking ID:', f"BK-{booking.id:06d}"],
        ['Check-in Date:', booking.start_date.strftime('%d %b %Y')],
        ['Check-out Date:', booking.end_date.strftime('%d %b %Y')],
        ['Rental Days:', str(days)],
        ['Rate per Day:', f"₹{car.price_per_day}"],
    ]
    
    booking_table = Table(booking_data, colWidths=[1.5*inch, 3.5*inch])
    booking_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    story.append(booking_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== PAYMENT BREAKDOWN =====
    story.append(Paragraph("PAYMENT SUMMARY", heading_style))
    
    subtotal = Decimal(days) * car.price_per_day
    gst_rate = Decimal('0.18')  # 18% GST
    gst_amount = subtotal * gst_rate
    total_with_gst = subtotal + gst_amount
    
    breakdown_data = [
        ['Description', 'Amount'],
        ['Subtotal (Base Fare)', f"₹{subtotal:,.2f}"],
        ['GST (18%)', f"₹{gst_amount:,.2f}"],
        ['Total Amount', f"₹{total_with_gst:,.2f}"],
        ['Amount Paid', f"₹{payment.amount:,.2f}"],
    ]
    
    breakdown_table = Table(breakdown_data, colWidths=[3*inch, 2*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#1E40AF')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9FAFB')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(breakdown_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== PAYMENT METHOD & TRANSACTION =====
    story.append(Paragraph("PAYMENT INFORMATION", heading_style))
    
    payment_info_data = [
        ['Payment Method:', 'Razorpay'],
        ['Payment ID:', payment.razorpay_payment_id or 'Pending'],
        ['Order ID:', payment.razorpay_order_id],
        ['Payment Date:', payment.updated_at.strftime('%d %b %Y, %H:%M:%S')],
        ['Status:', payment.get_status_display().upper()],
    ]
    
    payment_info_table = Table(payment_info_data, colWidths=[1.5*inch, 3.5*inch])
    payment_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    story.append(payment_info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # ===== FOOTER =====
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER,
    )
    
    story.append(Paragraph(
        "Thank you for booking with aSk.ren! For support, contact support@askren.com",
        footer_style
    ))
    story.append(Paragraph(
        f"Invoice generated on {datetime.now().strftime('%d %b %Y at %H:%M:%S')}",
        footer_style
    ))
    story.append(Paragraph(
        "This is a computer-generated invoice. No signature required.",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()
