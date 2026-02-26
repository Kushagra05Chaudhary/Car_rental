from django import forms
from .models import Car

CAR_TYPE_CHOICES = [
    ('', 'Select car type'),
    ('Sedan', 'Sedan'),
    ('SUV', 'SUV'),
    ('Hatchback', 'Hatchback'),
    ('Convertible', 'Convertible'),
    ('Coupe', 'Coupe'),
    ('Minivan', 'Minivan'),
    ('Pickup Truck', 'Pickup Truck'),
    ('Crossover', 'Crossover'),
    ('Electric', 'Electric'),
    ('Luxury', 'Luxury'),
]


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
            'car_type': forms.Select(
                choices=CAR_TYPE_CHOICES,
                attrs={
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white',
                }
            ),
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
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show "Select car type" as default for new cars (model default='Sedan' would otherwise pre-select it)
        if not self.instance.pk:
            self.fields['car_type'].initial = ''

    def clean_image(self):
        """Validate image file"""
        image = self.cleaned_data.get('image')
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
