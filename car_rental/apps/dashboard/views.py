from datetime import datetime as dt, timedelta
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser, OwnerRequest
from apps.cars.models import Car
from apps.bookings.models import Booking
from apps.payments.models import Payment
from .services import get_owner_dashboard_data

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Admin dashboard – shows platform-wide summary counts."""

    # Fetch base querysets once and reuse them for counting
    all_users     = CustomUser.objects.all()
    all_cars      = Car.objects.all()
    all_bookings  = Booking.objects.all()
    pending_reqs  = OwnerRequest.objects.filter(status='pending')

    context = {
        # Count regular users and owners separately
        'total_users':             all_users.filter(role='user').count(),
        'total_owners':            all_users.filter(role='owner').count(),

        # Car counts by status
        'total_cars':              all_cars.count(),
        'pending_cars':            all_cars.filter(status='pending').count(),
        'approved_cars':           all_cars.filter(status='approved').count(),

        # Owner requests waiting for admin approval
        'pending_owner_requests':  pending_reqs.count(),

        # Booking counts by status
        'total_bookings':          all_bookings.count(),
        'pending_bookings':        all_bookings.filter(status='pending').count(),
        'completed_bookings':      all_bookings.filter(status='completed').count(),
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
    car = get_object_or_404(Car, pk=pk)
    car.status = 'approved'
    car.save(update_fields=['status'])
    return redirect('admin_car_approval')

@login_required
@role_required('admin')
def reject_car(request, pk):
    car = get_object_or_404(Car, pk=pk)
    car.status = 'rejected'
    car.save(update_fields=['status'])
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


# ================= ADMIN ALL CARS =================

@login_required
@role_required('admin')
def admin_all_cars(request):
    """Admin view of all cars with search, status, and availability filters."""
    search_query        = request.GET.get('search', '')
    status_filter       = request.GET.get('status', '')
    availability_filter = request.GET.get('availability', '')

    # Start with all cars, joining owner info in one DB query
    cars = Car.objects.select_related('owner').all()

    # --- Search: collect matching IDs from each field, then filter by union ---
    if search_query:
        # Each filter returns IDs matching that specific field
        name_ids     = cars.filter(name__icontains=search_query).values_list('id', flat=True)
        brand_ids    = cars.filter(brand__icontains=search_query).values_list('id', flat=True)
        location_ids = cars.filter(location__icontains=search_query).values_list('id', flat=True)
        owner_ids    = cars.filter(owner__username__icontains=search_query).values_list('id', flat=True)

        # Combine all matched IDs into a single set (no duplicates)
        matched_ids = set(name_ids) | set(brand_ids) | set(location_ids) | set(owner_ids)
        cars = cars.filter(id__in=matched_ids)

    # Filter by car approval status if provided
    if status_filter:
        cars = cars.filter(status=status_filter)

    # Filter by availability if provided
    if availability_filter == 'available':
        cars = cars.filter(is_available=True)
    elif availability_filter == 'unavailable':
        cars = cars.filter(is_available=False)

    cars = cars.order_by('-created_at')

    # Reuse a single base queryset for all the sidebar counts
    all_cars      = Car.objects.all()
    approved_cars = all_cars.filter(status='approved')

    context = {
        'cars':               cars,
        'total_cars':         all_cars.count(),
        'approved_count':     approved_cars.count(),
        'pending_count':      all_cars.filter(status='pending').count(),
        'rejected_count':     all_cars.filter(status='rejected').count(),
        # Availability counts are scoped to approved cars only
        'available_count':    approved_cars.filter(is_available=True).count(),
        'unavailable_count':  approved_cars.filter(is_available=False).count(),
        'search_query':       search_query,
        'status_filter':      status_filter,
        'availability_filter': availability_filter,
    }
    return render(request, 'dashboard/admin_all_cars.html', context)


@login_required
@role_required('admin')
def admin_toggle_car_availability(request, pk):
    """Toggle a car's availability"""
    car = get_object_or_404(Car, pk=pk)
    car.is_available = not car.is_available
    car.save(update_fields=['is_available'])
    state = 'available' if car.is_available else 'unavailable'
    messages.success(request, f'"{car.name}" marked as {state}.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_all_cars'))


@login_required
@role_required('admin')
def admin_delete_car(request, pk):
    """Permanently delete a car listing"""
    car = get_object_or_404(Car, pk=pk)
    name = car.name
    car.delete()
    messages.success(request, f'"{name}" has been deleted.')
    return redirect('admin_all_cars')


# ================= ADMIN ALL BOOKINGS =================

@login_required
@role_required('admin')
def admin_all_bookings(request):
    """Admin view of every booking on the platform with search and status filter."""
    search_query  = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Fetch all bookings with related user and car data in one DB hit
    bookings = Booking.objects.select_related('user', 'car', 'car__owner').all()

    # --- Search: collect matching IDs from each field, then filter by union ---
    if search_query:
        user_ids      = bookings.filter(user__username__icontains=search_query).values_list('id', flat=True)
        email_ids     = bookings.filter(user__email__icontains=search_query).values_list('id', flat=True)
        car_ids       = bookings.filter(car__name__icontains=search_query).values_list('id', flat=True)
        car_owner_ids = bookings.filter(car__owner__username__icontains=search_query).values_list('id', flat=True)

        # Merge all matches into one set and filter
        matched_ids = set(user_ids) | set(email_ids) | set(car_ids) | set(car_owner_ids)
        bookings = bookings.filter(id__in=matched_ids)

    # Narrow down by booking status if a filter was selected
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    bookings = bookings.order_by('-created_at')

    # Reuse one base queryset for all sidebar counts
    all_bookings = Booking.objects.all()

    context = {
        'bookings':       bookings,
        'total_bookings': all_bookings.count(),
        'pending_count':  all_bookings.filter(status='pending').count(),
        'confirmed_count': all_bookings.filter(status='confirmed').count(),
        'completed_count': all_bookings.filter(status='completed').count(),
        'cancelled_count': all_bookings.filter(status='cancelled').count(),
        'rejected_count':  all_bookings.filter(status='rejected').count(),
        'search_query':   search_query,
        'status_filter':  status_filter,
    }
    return render(request, 'dashboard/admin_all_bookings.html', context)


@login_required
@role_required('owner')
def owner_dashboard(request):
    """Owner dashboard – collects data via get_owner_dashboard_data."""

    # All counts and earnings for this owner are built in the service layer
    dashboard_data = get_owner_dashboard_data(request.user)

    return render(request, 'dashboard/owner_dashboard.html', dashboard_data)


@login_required
@role_required('user')
def user_dashboard(request):
    """User dashboard – shows the logged-in user's booking summary."""

    # All bookings belonging to the current user
    user_bookings = Booking.objects.filter(user=request.user)

    context = {
        # Total number of bookings this user has made
        'my_bookings':       user_bookings.count(),
        # Bookings that are still in progress (pending or confirmed)
        'active_bookings':   user_bookings.filter(status='pending').count()
                             + user_bookings.filter(status='confirmed').count(),
        'completed_bookings': user_bookings.filter(status='completed').count(),
        # Last 5 bookings for the recent activity table
        'recent_bookings':   user_bookings.select_related('car').order_by('-created_at')[:5],
    }

    return render(request, 'dashboard/user_dashboard.html', context)


# ================= ADMIN USER MANAGEMENT =================

@login_required
@role_required('admin')
def admin_users_management(request):
    """Manage all users – supports search by username, email, or first name."""
    search_query = request.GET.get('search', '')
    role_filter  = request.GET.get('role', '')

    # Start with all users
    users = CustomUser.objects.all()

    # --- Search: gather matching IDs field by field, then combine ---
    if search_query:
        username_ids   = users.filter(username__icontains=search_query).values_list('id', flat=True)
        email_ids      = users.filter(email__icontains=search_query).values_list('id', flat=True)
        first_name_ids = users.filter(first_name__icontains=search_query).values_list('id', flat=True)

        matched_ids = set(username_ids) | set(email_ids) | set(first_name_ids)
        users = users.filter(id__in=matched_ids)

    # Optionally narrow down to a specific role
    if role_filter:
        users = users.filter(role=role_filter)

    users = users.order_by('-created_at')

    # Reuse a base queryset for sidebar counts so we avoid extra queries
    all_users = CustomUser.objects.all()

    context = {
        'users':        users,
        'total_users':  all_users.count(),
        'users_count':  all_users.filter(role='user').count(),
        'owners_count': all_users.filter(role='owner').count(),
        'admins_count': all_users.filter(role='admin').count(),
        'search_query': search_query,
        'role_filter':  role_filter,
    }

    return render(request, 'dashboard/admin_users_management.html', context)


@login_required
@role_required('admin')
def admin_reports(request):
    """Admin reports – platform-wide analytics and revenue summary."""

    # ----- Date helpers -----
    thirty_days_ago = timezone.now() - timedelta(days=30)
    six_months_ago  = timezone.now() - timedelta(days=180)

    COMMISSION_RATE = Decimal('0.10')  # Platform takes 10% of net revenue

    # ----- Booking counts -----
    # Reuse one base queryset so we hit the DB once per .count() call
    all_bookings       = Booking.objects.all()
    total_bookings     = all_bookings.count()
    completed_bookings = all_bookings.filter(status='completed').count()
    pending_bookings   = all_bookings.filter(status='pending').count()
    confirmed_bookings = all_bookings.filter(status='confirmed').count()

    # ----- Revenue calculations -----
    # Completed payments = gross money collected
    completed_payments = Payment.objects.filter(status='completed')
    refunded_payments  = Payment.objects.filter(status='refunded')

    gross_revenue  = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_refunded = refunded_payments.aggregate(total=Sum('amount'))['total']  or Decimal('0')
    refund_count   = refunded_payments.count()
    # Net revenue = what was collected minus what was returned
    total_revenue  = gross_revenue - total_refunded

    # Same calculation scoped to the last 30 days
    gross_last_30     = completed_payments.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    refunded_last_30  = refunded_payments.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))['total']  or Decimal('0')
    revenue_last_30_days = gross_last_30 - refunded_last_30

    # Platform commission = 10% of net revenue
    commission_earned  = total_revenue * COMMISSION_RATE
    commission_30_days = revenue_last_30_days * COMMISSION_RATE

    # ----- User and owner stats -----
    all_users         = CustomUser.objects.all()
    new_users_30_days = all_users.filter(role='user', created_at__gte=thirty_days_ago).count()
    total_owners      = all_users.filter(role='owner').count()
    new_owners_30_days = all_users.filter(role='owner', created_at__gte=thirty_days_ago).count()

    # ----- Car stats -----
    all_cars      = Car.objects.all()
    approved_cars = all_cars.filter(status='approved').count()
    pending_cars  = all_cars.filter(status='pending').count()
    rejected_cars = all_cars.filter(status='rejected').count()

    # ----- Monthly net revenue chart (last 6 months) -----
    # Group completed payments by calendar month and sum them
    monthly_completed_qs = (
        Payment.objects.filter(status='completed', created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    # Group refunded payments by month so we can subtract them
    monthly_refunded_qs = (
        Payment.objects.filter(status='refunded', created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
    )

    # Build a dict {month: refunded_amount} for quick lookup
    refunded_by_month = {entry['month']: float(entry['total']) for entry in monthly_refunded_qs}

    revenue_months = [entry['month'].strftime('%b %Y') for entry in monthly_completed_qs]
    revenue_values = [
        round(float(entry['total']) - refunded_by_month.get(entry['month'], 0), 2)
        for entry in monthly_completed_qs
    ]
    commission_values = [round(v * 0.10, 2) for v in revenue_values]

    # ----- Booking status breakdown for chart -----
    # Returns a list like [{'status': 'completed', 'count': 42}, ...]
    booking_stats = all_bookings.values('status').annotate(count=Count('id'))

    # ----- Top 5 earning owners -----
    # Sum completed payment amounts grouped by the car's owner
    top_owners_qs = (
        Payment.objects.filter(status='completed')
        .values('booking__car__owner')
        .annotate(total_earnings=Sum('amount'))
        .order_by('-total_earnings')[:5]
    )

    # Attach the actual owner object to each result for template display
    top_owners_list = []
    for row in top_owners_qs:
        owner_id = row['booking__car__owner']
        if owner_id:
            try:
                owner = CustomUser.objects.get(id=owner_id, role='owner')
                top_owners_list.append({
                    'owner':          owner,
                    'total_earnings': row['total_earnings'],
                })
            except CustomUser.DoesNotExist:
                pass

    context = {
        'total_bookings':      total_bookings,
        'completed_bookings':  completed_bookings,
        'pending_bookings':    pending_bookings,
        'confirmed_bookings':  confirmed_bookings,
        'total_revenue':       total_revenue,
        'revenue_last_30_days': revenue_last_30_days,
        'gross_revenue':       gross_revenue,
        'total_refunded':      total_refunded,
        'refund_count':        refund_count,
        'commission_earned':   commission_earned,
        'commission_30_days':  commission_30_days,
        'new_users_30_days':   new_users_30_days,
        'approved_cars':       approved_cars,
        'pending_cars':        pending_cars,
        'rejected_cars':       rejected_cars,
        'total_owners':        total_owners,
        'new_owners_30_days':  new_owners_30_days,
        'booking_stats':       booking_stats,
        'top_owners':          top_owners_list,
        'revenue_months':      revenue_months,
        'revenue_values':      revenue_values,
        'commission_values':   commission_values,
    }

    return render(request, 'dashboard/admin_reports.html', context)


@login_required
@role_required('admin')
def download_report(request):
    """Generate and download the admin analytics report as a PDF file."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    COMMISSION_RATE = Decimal('0.10')
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # ----- PDF title and generation date -----
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, spaceAfter=6)
    story.append(Paragraph('aSk.ren Analytics Report', title_style))
    story.append(Paragraph(f'Generated on {dt.now().strftime("%d %b %Y, %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # ----- Revenue section -----
    # Fetch completed and refunded payment querysets once, reuse for both all-time and 30-day calcs
    completed_payments = Payment.objects.filter(status='completed')
    refunded_payments  = Payment.objects.filter(status='refunded')

    gross_revenue  = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_refunded = refunded_payments.aggregate(total=Sum('amount'))['total']  or Decimal('0')
    refund_count   = refunded_payments.count()
    total_revenue  = gross_revenue - total_refunded

    # Narrow the same querysets to the last 30 days
    gross_30     = completed_payments.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    refunded_30  = refunded_payments.filter(created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))['total']  or Decimal('0')
    revenue_30   = gross_30 - refunded_30
    commission   = total_revenue * COMMISSION_RATE
    commission_30 = revenue_30 * COMMISSION_RATE

    story.append(Paragraph('Revenue Summary', styles['Heading2']))
    rev_data = [
        ['Metric', 'Amount'],
        ['Gross Revenue (Completed)', f'Rs. {gross_revenue:.0f}'],
        ['Total Refunded', f'- Rs. {total_refunded:.0f}  ({refund_count} refunds)'],
        ['Net Revenue', f'Rs. {total_revenue:.0f}'],
        ['Net Revenue (Last 30 Days)', f'Rs. {revenue_30:.0f}'],
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

    # ----- Booking section (reuse one base queryset) -----
    story.append(Paragraph('Booking Statistics', styles['Heading2']))
    all_bookings = Booking.objects.all()
    bk_data = [
        ['Status', 'Count'],
        ['Total Bookings', str(all_bookings.count())],
        ['Completed',      str(all_bookings.filter(status='completed').count())],
        ['Confirmed',      str(all_bookings.filter(status='confirmed').count())],
        ['Pending',        str(all_bookings.filter(status='pending').count())],
        ['Cancelled',      str(all_bookings.filter(status='cancelled').count())],
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

    # ----- Platform overview section (reuse base querysets) -----
    story.append(Paragraph('Platform Overview', styles['Heading2']))
    all_cars  = Car.objects.all()
    all_users = CustomUser.objects.all()
    ov_data = [
        ['Metric', 'Count'],
        ['Approved Cars',       str(all_cars.filter(status='approved').count())],
        ['Pending Cars',        str(all_cars.filter(status='pending').count())],
        ['Rejected Cars',       str(all_cars.filter(status='rejected').count())],
        ['Total Owners',        str(all_users.filter(role='owner').count())],
        ['Total Users',         str(all_users.filter(role='user').count())],
        ['New Users (30 Days)', str(all_users.filter(role='user', created_at__gte=thirty_days_ago).count())],
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
    filename = f'report_{dt.now().strftime("%Y%m%d_%H%M")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('admin')
def admin_transactions(request):
    """Admin transactions page – full payment history with search and filters."""
    search_query  = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('method', '')

    # Fetch all payments, joining user and car info in one DB query
    payments = Payment.objects.select_related('user', 'booking__car').all()

    # --- Search: gather matching IDs field by field, then combine ---
    if search_query:
        txn_ids  = payments.filter(transaction_id__icontains=search_query).values_list('id', flat=True)
        user_ids = payments.filter(user__username__icontains=search_query).values_list('id', flat=True)
        email_ids = payments.filter(user__email__icontains=search_query).values_list('id', flat=True)
        car_ids  = payments.filter(booking__car__name__icontains=search_query).values_list('id', flat=True)

        matched_ids = set(txn_ids) | set(user_ids) | set(email_ids) | set(car_ids)
        payments = payments.filter(id__in=matched_ids)

    # Filter by payment status if selected
    if status_filter:
        payments = payments.filter(status=status_filter)

    # Filter by payment method if selected (case-insensitive)
    if method_filter:
        payments = payments.filter(payment_method__iexact=method_filter)

    payments = payments.order_by('-created_at')

    COMMISSION_RATE = Decimal('0.10')

    # Reuse base queryset for revenue totals to avoid extra round-trips
    all_payments       = Payment.objects.all()
    completed_payments = all_payments.filter(status='completed')
    refunded_payments  = all_payments.filter(status='refunded')

    total_revenue     = all_payments.aggregate(total=Sum('amount'))['total'] or 0
    completed_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or 0
    refunded_revenue  = refunded_payments.aggregate(total=Sum('amount'))['total'] or 0
    # Commission is calculated only on successfully completed payments
    commission_earned = (Decimal(str(completed_revenue))) * COMMISSION_RATE

    context = {
        'payments':           payments,
        'total_transactions': all_payments.count(),
        'completed_count':    completed_payments.count(),
        'pending_count':      all_payments.filter(status='pending').count(),
        'refunded_count':     refunded_payments.count(),
        'failed_count':       all_payments.filter(status='failed').count(),
        'total_revenue':      total_revenue,
        'completed_revenue':  completed_revenue,
        'refunded_revenue':   refunded_revenue,
        'commission_earned':  commission_earned,
        'search_query':       search_query,
        'status_filter':      status_filter,
        'method_filter':      method_filter,
    }

    return render(request, 'dashboard/admin_transactions.html', context)


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
