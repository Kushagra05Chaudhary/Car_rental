from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
import dns.resolver

class RegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Format validation
        try:
            validate_email(email)
        except:
            raise ValidationError("Invalid email format.")

        # Unique validation
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")

        # Domain validation
        domain = email.split('@')[1]
        try:
            dns.resolver.resolve(domain, 'MX')
        except:
            raise ValidationError("Email domain does not exist.")

        return email