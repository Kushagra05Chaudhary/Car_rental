from django import forms
from .models import Car


class OwnerCarForm(forms.ModelForm):
    """Form for owner to add/edit cars"""
    
    class Meta:
        model = Car
        fields = ['name', 'brand', 'car_type', 'location', 'price_per_day', 'seats', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Car name (e.g., Honda Civic)'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Brand (e.g., Honda)'
            }),
            'car_type': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Car type (e.g., Sedan, SUV)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Pickup location'
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Price per day',
                'step': '0.01'
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Number of seats',
                'min': '1'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': 'image/jpeg,image/png'
            }),
        }
    
    def clean_image(self):
        """Validate image file"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image size must not exceed 5MB.')
            
            # Check file type
            valid_types = ['image/jpeg', 'image/png']
            if image.content_type not in valid_types:
                raise forms.ValidationError('Only JPG and PNG images are allowed.')
        
        return image
    
    def clean_price_per_day(self):
        """Validate price"""
        price = self.cleaned_data.get('price_per_day')
        
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        
        return price
    
    def clean_seats(self):
        """Validate seats"""
        seats = self.cleaned_data.get('seats')
        
        if seats and seats < 1:
            raise forms.ValidationError('Car must have at least 1 seat.')
        
        return seats
