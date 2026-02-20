from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import RegisterForm
from .models import CustomUser, OTP
from .models import OwnerRequest
from apps.bookings.tasks import send_otp_email
import random


# ================= REGISTER WITH OTP =================

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():

            # Store user data temporarily in session
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password1'],
                'phone': form.cleaned_data.get('phone', ''),
            }

            # Generate OTP
            otp = str(random.randint(100000, 999999))

            request.session['pending_registration'] = user_data
            request.session['registration_otp'] = otp

            # Send OTP asynchronously
            send_otp_email(user_data['email'], otp)

            messages.success(request, 'Check your email for the OTP.')
            return redirect('verify_otp')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# ================= NORMAL LOGIN =================

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_redirect')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


# ================= DASHBOARD REDIRECT =================

@login_required
def dashboard_redirect(request):
    # Superusers and admins can access admin dashboard
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('admin_dashboard')
    # Owners get the owner dashboard
    elif request.user.role == 'owner':
        return redirect('owner_dashboard')
    # Regular users get the user dashboard
    else:
        return redirect('user_dashboard')


# ================= LOGOUT =================

def logout_view(request):
    logout(request)
    return redirect('login')


# ================= OTP LOGIN (Existing User) =================

def send_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            return redirect('otp_login')

        otp = str(random.randint(100000, 999999))
        OTP.objects.create(user=user, code=otp)

        # Send OTP asynchronously
        send_otp_email(user.email, otp)

        request.session['otp_user'] = user.id
        messages.success(request, 'OTP sent to your email!')
        return redirect('verify_otp')

    return render(request, 'accounts/send_otp.html')


# ================= VERIFY OTP =================

def verify_otp(request):

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')

        # ---------- Registration OTP ----------
        if 'pending_registration' in request.session:

            stored_otp = request.session.get('registration_otp')

            if otp_entered == stored_otp:

                user_data = request.session['pending_registration']

                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    phone=user_data.get('phone', ''),
                    role='user',  # DEFAULT ROLE
                    is_active=True,
                    is_email_verified=True
                )

                # Clean session
                del request.session['pending_registration']
                del request.session['registration_otp']

                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('dashboard_redirect')

            else:
                messages.error(request, 'Invalid OTP.')

        # ---------- Login OTP ----------
        else:
            user_id = request.session.get('otp_user')

            if not user_id:
                return redirect('otp_login')

            user = CustomUser.objects.get(id=user_id)

            if OTP.objects.filter(user=user, code=otp_entered).exists():
                OTP.objects.filter(user=user, code=otp_entered).delete()
                login(request, user)
                return redirect('dashboard_redirect')
            else:
                messages.error(request, 'Invalid OTP.')

    return render(request, 'accounts/verify_otp.html')


# ================= RESEND REGISTRATION OTP =================

def resend_registration_otp(request):

    if 'pending_registration' in request.session:

        user_data = request.session['pending_registration']

        otp = str(random.randint(100000, 999999))
        request.session['registration_otp'] = otp

        send_mail(
            'Verify Your Account - OTP',
            f'Your new OTP is: {otp}',
            settings.EMAIL_HOST_USER,
            [user_data['email']],
        )

        messages.success(request, 'New OTP sent!')
        return redirect('verify_otp')

    return redirect('register')


@login_required
def become_owner(request):

    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, "Admins cannot become owners.")
        return redirect('admin_dashboard')

    if request.user.role != 'user':
        messages.error(request, "You are already an owner.")
        return redirect('dashboard_redirect')

    # Prevent duplicate request
    if OwnerRequest.objects.filter(user=request.user, status='pending').exists():
        messages.warning(request, "You already have a pending request.")
        return redirect('user_dashboard')

    OwnerRequest.objects.create(user=request.user)

    messages.success(request, "Owner request submitted. Wait for admin approval.")
    return redirect('user_dashboard')


# ================= OWNER PROFILE =================

@login_required
def owner_profile_view(request):
    """View owner profile"""
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins cannot access owner profile.')
        return redirect('admin_dashboard')
    
    if request.user.role != 'owner':
        messages.error(request, 'Only owners can access this page.')
        return redirect('dashboard_redirect')
    
    return render(request, 'accounts/owner_profile.html', {'user': request.user})


@login_required
def owner_profile_edit_view(request):
    """Edit owner profile"""
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins cannot access owner profile.')
        return redirect('admin_dashboard')
    
    if request.user.role != 'owner':
        messages.error(request, 'Only owners can access this page.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        from .forms import OwnerProfileForm
        form = OwnerProfileForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('owner_profile')
    else:
        from .forms import OwnerProfileForm
        form = OwnerProfileForm(instance=request.user)
    
    return render(request, 'accounts/owner_profile_edit.html', {'form': form})


@login_required
def owner_change_password_view(request):
    """Change password for owner"""
    if request.user.is_superuser or request.user.role == 'admin':
        messages.error(request, 'Admins cannot access owner profile.')
        return redirect('admin_dashboard')
    
    if request.user.role != 'owner':
        messages.error(request, 'Only owners can access this page.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        from .forms import OwnerPasswordChangeForm
        form = OwnerPasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('owner_profile')
    else:
        from .forms import OwnerPasswordChangeForm
        form = OwnerPasswordChangeForm(request.user)
    
    return render(request, 'accounts/owner_change_password.html', {'form': form})