from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(*roles):
    """
    Decorator to check if user has the required role.
    Usage: @role_required('admin', 'owner')
    Superusers can access admin features. Admins can only access admin features.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in to access this page.')
                return redirect('login')

            # Superusers can access admin features
            if request.user.is_superuser:
                if 'admin' in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'Superusers can only access admin features.')
                    return redirect('admin_dashboard')

            # Admins can only access admin features
            if request.user.role == 'admin' and 'admin' not in roles:
                messages.error(request, 'Admins can only access admin features.')
                return redirect('admin_dashboard')
            
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('login')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
