from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from .models import CustomUser, OTP
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import random
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Don't save user yet - store data in session for OTP verification
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password1'],
                'phone': form.cleaned_data.get('phone', ''),
                'role': form.cleaned_data.get('role', 'user'),
            }
            
            # Generate and send OTP
            otp = str(random.randint(100000, 999999))
            
            # Store registration data and OTP in session
            request.session['pending_registration'] = user_data
            request.session['registration_otp'] = otp
            request.session['otp_email'] = user_data['email']
            
            send_mail(
                'Verify Your Account - OTP',
                f'Your OTP for account verification is: {otp}',
                settings.EMAIL_HOST_USER,
                [user_data['email']],
            )

            messages.success(request, 'Registration successful! Please check your email for the OTP.')
            return redirect('verify_otp')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})



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


@login_required
def dashboard_redirect(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'owner':
        return redirect('owner_dashboard')
    else:
        return redirect('user_dashboard')


def logout_view(request):
    logout(request)
    return redirect('login')

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

        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [user.email],
        )

        request.session['otp_user'] = user.id
        messages.success(request, 'OTP sent to your email!')
        return redirect('verify_otp')

    return render(request, 'accounts/send_otp.html')

def verify_otp(request):
    # Check if user came from registration but session expired
    if request.method == 'GET':
        if 'pending_registration' not in request.session and 'otp_user' not in request.session:
            messages.warning(request, 'Session expired. Please register or login again.')
            return redirect('register')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        
        # Check if this is a new registration
        if 'pending_registration' in request.session:
            stored_otp = request.session.get('registration_otp')
            
            if otp_entered == stored_otp:
                # Create the user now
                user_data = request.session['pending_registration']
                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    phone=user_data.get('phone', ''),
                    role=user_data.get('role', 'user'),
                    is_active=True,
                    is_email_verified=True
                )
                
                # Clean up session
                del request.session['pending_registration']
                del request.session['registration_otp']
                if 'otp_email' in request.session:
                    del request.session['otp_email']
                
                # Log the user in
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome aboard.')
                return redirect('dashboard_redirect')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        
        # For existing users logging in via OTP
        else:
            user_id = request.session.get('otp_user')
            if not user_id:
                return redirect('otp_login')

            user = CustomUser.objects.get(id=user_id)

            if OTP.objects.filter(user=user, code=otp_entered).exists():
                # Delete used OTP
                OTP.objects.filter(user=user, code=otp_entered).delete()
                
                # Set backend for login
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('dashboard_redirect')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'accounts/verify_otp.html')


@csrf_exempt
def resend_registration_otp(request):
    """Resend OTP for pending registration"""
    if 'pending_registration' in request.session:
        user_data = request.session['pending_registration']
        
        # Generate new OTP
        otp = str(random.randint(100000, 999999))
        request.session['registration_otp'] = otp
        
        send_mail(
            'Verify Your Account - OTP',
            f'Your new OTP for account verification is: {otp}',
            settings.EMAIL_HOST_USER,
            [user_data['email']],
        )
        
        messages.success(request, 'A new OTP has been sent to your email!')
        return redirect('verify_otp')
    
    # If no pending registration, redirect to send OTP for login
    return redirect('otp_login')
