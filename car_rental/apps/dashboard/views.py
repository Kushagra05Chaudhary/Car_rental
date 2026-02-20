from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser, OwnerRequest
from apps.cars.models import Car
from apps.bookings.models import Booking
from apps.payments.models import Payment
from .services import DashboardService

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'total_users': CustomUser.objects.filter(role='user').count(),
        'total_owners': CustomUser.objects.filter(role='owner').count(),
        'total_cars': Car.objects.count(),
        'pending_cars': Car.objects.filter(status='pending').count(),
        'pending_owner_requests': OwnerRequest.objects.filter(status='pending').count(),
        'approved_cars': Car.objects.filter(status='approved').count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'completed_bookings': Booking.objects.filter(status='completed').count(),
    }

    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@role_required('admin')
def admin_car_approval(request):

    cars = Car.objects.filter(status='pending')

    return render(request, 'dashboard/admin_car_approval.html', {
        'cars': cars
    })

@login_required
@role_required('admin')
def approve_car(request, pk):
    car = Car.objects.get(pk=pk)
    car.status = 'approved'
    car.save()
    return redirect('admin_car_approval')

@login_required
@role_required('admin')
def reject_car(request, pk):
    car = Car.objects.get(pk=pk)
    car.status = 'rejected'
    car.save()
    return redirect('admin_car_approval')

@login_required
@role_required('admin')
def admin_owner_requests(request):

    requests = OwnerRequest.objects.filter(status='pending')

    return render(request, 'dashboard/admin_owner_requests.html', {
        'requests': requests
    })
@login_required
@role_required('admin')
def approve_owner(request, pk):
    try:
        req = OwnerRequest.objects.get(pk=pk)
        req.status = 'approved'
        req.save()

        user = req.user
        user.role = 'owner'
        user.save()
        
        messages.success(request, f'{user.username} has been approved as an owner.')
    except OwnerRequest.DoesNotExist:
        messages.error(request, 'Request not found.')

    return redirect('admin_owner_requests')


@login_required
@role_required('admin')
def reject_owner(request, pk):
    try:
        req = OwnerRequest.objects.get(pk=pk)
        username = req.user.username
        req.status = 'rejected'
        req.save()
        
        messages.success(request, f'{username}\'s owner request has been rejected.')
    except OwnerRequest.DoesNotExist:
        messages.error(request, 'Request not found.')

    return redirect('admin_owner_requests')
    
@login_required
@role_required('owner')
def owner_dashboard(request):
    """Owner dashboard view with comprehensive statistics"""
    
    # Get all dashboard data using service
    dashboard_data = DashboardService.get_owner_dashboard_data(request.user)
    
    return render(request, 'dashboard/owner_dashboard.html', dashboard_data)


@login_required
@role_required('user')
def user_dashboard(request):
    """User dashboard view"""
    user_bookings = Booking.objects.filter(user=request.user)
    
    context = {
        'my_bookings': user_bookings.count(),
        'active_bookings': user_bookings.filter(status__in=['pending', 'confirmed']).count(),
        'completed_bookings': user_bookings.filter(status='completed').count(),
        'recent_bookings': user_bookings.order_by('-created_at')[:5],
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)


# ================= ADMIN USER MANAGEMENT =================

@login_required
@role_required('admin')
def admin_users_management(request):
    """Manage all users in the system"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = CustomUser.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    users = users.order_by('-created_at')
    
    context = {
        'users': users,
        'total_users': CustomUser.objects.count(),
        'users_count': CustomUser.objects.filter(role='user').count(),
        'owners_count': CustomUser.objects.filter(role='owner').count(),
        'admins_count': CustomUser.objects.filter(role='admin').count(),
        'search_query': search_query,
        'role_filter': role_filter,
    }
    
    return render(request, 'dashboard/admin_users_management.html', context)


@login_required
@role_required('admin')
def admin_reports(request):
    """Admin reports and analytics"""
    
    # Date range for last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Booking Statistics
    total_bookings = Booking.objects.count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    
    # Revenue Statistics
    from decimal import Decimal
    COMMISSION_RATE = Decimal('0.10')  # 10%
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    revenue_last_30_days = Payment.objects.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    commission_earned = total_revenue * COMMISSION_RATE
    commission_30_days = revenue_last_30_days * COMMISSION_RATE
    
    # User Statistics
    new_users_30_days = CustomUser.objects.filter(
        created_at__gte=thirty_days_ago,
        role='user'
    ).count()
    
    # Car Statistics
    approved_cars = Car.objects.filter(status='approved').count()
    pending_cars = Car.objects.filter(status='pending').count()
    rejected_cars = Car.objects.filter(status='rejected').count()
    
    # Owner Statistics
    total_owners = CustomUser.objects.filter(role='owner').count()
    new_owners_30_days = CustomUser.objects.filter(
        created_at__gte=thirty_days_ago,
        role='owner'
    ).count()
    
    # Monthly revenue for last 6 months
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_revenue_qs = (
        Payment.objects.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    revenue_months = [entry['month'].strftime('%b %Y') for entry in monthly_revenue_qs]
    revenue_values = [float(entry['total']) for entry in monthly_revenue_qs]
    commission_values = [round(v * 0.10, 2) for v in revenue_values]

    # Booking status breakdown
    booking_stats = Booking.objects.values('status').annotate(count=Count('id'))
    
    # Top earning owners - simplified query
    top_owners = Payment.objects.filter(
        status='completed'
    ).values('booking__car__owner').annotate(
        total_earnings=Sum('amount')
    ).order_by('-total_earnings')[:5]
    
    # Get owner usernames for display
    top_owners_list = []
    for owner_data in top_owners:
        owner_id = owner_data['booking__car__owner']
        if owner_id:
            try:
                owner = CustomUser.objects.get(id=owner_id, role='owner')
                top_owners_list.append({
                    'owner': owner,
                    'total_earnings': owner_data['total_earnings']
                })
            except CustomUser.DoesNotExist:
                pass
    
    context = {
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'total_revenue': total_revenue,
        'revenue_last_30_days': revenue_last_30_days,
        'commission_earned': commission_earned,
        'commission_30_days': commission_30_days,
        'new_users_30_days': new_users_30_days,
        'approved_cars': approved_cars,
        'pending_cars': pending_cars,
        'rejected_cars': rejected_cars,
        'total_owners': total_owners,
        'new_owners_30_days': new_owners_30_days,
        'booking_stats': booking_stats,
        'top_owners': top_owners_list,
        'revenue_months': revenue_months,
        'revenue_values': revenue_values,
        'commission_values': commission_values,
    }
    
    return render(request, 'dashboard/admin_reports.html', context)


@login_required
@role_required('admin')
def download_report(request):
    """Download admin analytics report as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from io import BytesIO
    from decimal import Decimal
    import datetime

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    COMMISSION_RATE = Decimal('0.10')
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Title
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, spaceAfter=6)
    story.append(Paragraph('aSk.ren Analytics Report', title_style))
    story.append(Paragraph(f'Generated on {datetime.datetime.now().strftime("%d %b %Y, %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Revenue
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    revenue_30 = Payment.objects.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    commission = total_revenue * COMMISSION_RATE
    commission_30 = revenue_30 * COMMISSION_RATE

    story.append(Paragraph('Revenue Summary', styles['Heading2']))
    rev_data = [
        ['Metric', 'Amount'],
        ['Total Revenue', f'Rs. {total_revenue:.0f}'],
        ['Revenue (Last 30 Days)', f'Rs. {revenue_30:.0f}'],
        ['Commission Earned (10%)', f'Rs. {commission:.0f}'],
        ['Commission (Last 30 Days)', f'Rs. {commission_30:.0f}'],
    ]
    t = Table(rev_data, colWidths=[10*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Bookings
    story.append(Paragraph('Booking Statistics', styles['Heading2']))
    bk_data = [
        ['Status', 'Count'],
        ['Total Bookings', str(Booking.objects.count())],
        ['Completed', str(Booking.objects.filter(status='completed').count())],
        ['Confirmed', str(Booking.objects.filter(status='confirmed').count())],
        ['Pending', str(Booking.objects.filter(status='pending').count())],
        ['Cancelled', str(Booking.objects.filter(status='cancelled').count())],
    ]
    t2 = Table(bk_data, colWidths=[10*cm, 7*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.5*cm))

    # Cars & Users
    story.append(Paragraph('Platform Overview', styles['Heading2']))
    ov_data = [
        ['Metric', 'Count'],
        ['Approved Cars', str(Car.objects.filter(status='approved').count())],
        ['Pending Cars', str(Car.objects.filter(status='pending').count())],
        ['Rejected Cars', str(Car.objects.filter(status='rejected').count())],
        ['Total Owners', str(CustomUser.objects.filter(role='owner').count())],
        ['Total Users', str(CustomUser.objects.filter(role='user').count())],
        ['New Users (30 Days)', str(CustomUser.objects.filter(role='user', created_at__gte=thirty_days_ago).count())],
    ]
    t3 = Table(ov_data, colWidths=[10*cm, 7*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t3)

    doc.build(story)
    buffer.seek(0)
    filename = f'report_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('admin')
def block_user(request, user_id):
    """Block/Unblock a user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been blocked.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_users_management')


@login_required
@role_required('admin')
def unblock_user(request, user_id):
    """Unblock a user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been unblocked.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_users_management')


@login_required
@role_required('admin')
def delete_user(request, user_id):
    """Delete a user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'User {username} has been deleted.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admin_users_management')


@login_required
@role_required('admin')
def remove_owner(request, user_id):
    """Remove owner role from a user (change to regular user)"""
    try:
        user = CustomUser.objects.get(id=user_id, role='owner')
        user.role = 'user'
        user.save()
        messages.success(request, f'User {user.username} is no longer an owner.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Owner not found.')
    
    return redirect('admin_users_management')
