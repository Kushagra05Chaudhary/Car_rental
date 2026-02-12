from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from .models import CustomUser, OTP
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
import random
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # user cannot login yet
            user.save()

            token = get_random_string(50)
            request.session['verify_token'] = token
            request.session['verify_user'] = user.id

            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[token])
            )

            send_mail(
                'Verify Your Email',
                f'Click the link to verify your email: {verification_link}',
                settings.EMAIL_HOST_USER,
                [user.email],
            )

            return render(request, 'accounts/check_email.html')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

def verify_email(request, token):
    session_token = request.session.get('verify_token')
    user_id = request.session.get('verify_user')

    if token == session_token and user_id:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = True
        user.is_email_verified = True
        user.save()

        return render(request, 'accounts/email_verified.html')

    return redirect('register')

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
        return redirect('/admin-dashboard/')
    elif request.user.role == 'owner':
        return redirect('/owner-dashboard/')
    else:
        return redirect('/user-dashboard/')


def logout_view(request):
    logout(request)
    return redirect('login')

def send_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return redirect('login')

        otp = str(random.randint(100000, 999999))

        OTP.objects.create(user=user, code=otp)

        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [user.email],
        )

        request.session['otp_user'] = user.id
        return redirect('verify_otp')

    return render(request, 'accounts/send_otp.html')

def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        user_id = request.session.get('otp_user')
        if not user_id:
            return redirect('otp_login')

        user = CustomUser.objects.get(id=user_id)

        if OTP.objects.filter(user=user, code=otp_entered).exists():
            login(request, user)
            return redirect('dashboard_redirect')

    return render(request, 'accounts/verify_otp.html')
