from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required


@login_required
@role_required('admin')
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html')


@login_required
@role_required('owner')
def owner_dashboard(request):
    return render(request, 'dashboard/owner_dashboard.html')


@login_required
@role_required('user')
def user_dashboard(request):
    return render(request, 'dashboard/user_dashboard.html')
