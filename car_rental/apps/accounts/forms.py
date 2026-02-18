from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser
import dns.resolver

class RegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password1', 'password2']

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


class OwnerProfileForm(forms.ModelForm):
    """Form for owner to update profile"""
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'driving_license', 'insurance_document']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Last Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+1 (555) 000-0000'
            }),
            'driving_license': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'insurance_document': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
    
    def clean_driving_license(self):
        """Validate driving license file"""
        file = self.cleaned_data.get('driving_license')
        
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must not exceed 5MB.')
            
            # Check file type
            valid_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in valid_types:
                raise ValidationError('Only PDF, JPG, and PNG files are allowed.')
        
        return file
    
    def clean_insurance_document(self):
        """Validate insurance document file"""
        file = self.cleaned_data.get('insurance_document')
        
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must not exceed 5MB.')
            
            # Check file type
            valid_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in valid_types:
                raise ValidationError('Only PDF, JPG, and PNG files are allowed.')
        
        return file


class OwnerPasswordChangeForm(PasswordChangeForm):
    """Custom password change form for owners"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        })