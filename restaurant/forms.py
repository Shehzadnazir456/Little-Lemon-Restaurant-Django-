from django import forms
from django.core.exceptions import ValidationError
from .models import Reservation, Order


# ---------------------------------------------------------------------------
# Reservation form
# ---------------------------------------------------------------------------

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['name', 'email', 'contact', 'time', 'count', 'item', 'notes']
        widgets = {
            'time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-input'},
                format='%Y-%m-%dT%H:%M',
            ),
            'name':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your full name'}),
            'email':   forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}),
            'contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+92 300 1234567'}),
            'count':   forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 20}),
            'notes':   forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Any special requests?'}),
            'item':    forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'count': 'Party size',
            'item':  'Pre-order a dish (optional)',
            'time':  'Date & time',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # datetime-local needs this input format
        self.fields['time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['item'].required = False


# ---------------------------------------------------------------------------
# Order / checkout form
# ---------------------------------------------------------------------------

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'email', 'phone', 'order_type', 'delivery_address', 'party_size', 'notes']
        widgets = {
            'customer_name':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your full name'}),
            'email':            forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}),
            'phone':            forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+92 300 0000000'}),
            'order_type':       forms.RadioSelect(attrs={'class': 'radio-group'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Street, city, postal code'}),
            'party_size':       forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 20, 'placeholder': 'Number of guests'}),
            'notes':            forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Allergies, special requests…'}),
        }
        labels = {
            'customer_name': 'Your name',
            'order_type':    'Order type',
        }

    def clean(self):
        cleaned = super().clean()
        order_type = cleaned.get('order_type')
        address = cleaned.get('delivery_address', '').strip()
        party = cleaned.get('party_size')

        if order_type == Order.OrderType.TAKEAWAY and not address:
            self.add_error('delivery_address', 'A delivery address is required for takeaway orders.')

        if order_type == Order.OrderType.DINE_IN and not party:
            self.add_error('party_size', 'Please enter your party size for dine-in orders.')

        return cleaned


# ---------------------------------------------------------------------------
# Order status lookup form (no login)
# ---------------------------------------------------------------------------

class OrderLookupForm(forms.Form):
    order_id = forms.IntegerField(
        label='Order number',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 42'}),
    )
    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'The email used when ordering'}),
    )


# ---------------------------------------------------------------------------
# Dashboard: update order status
# ---------------------------------------------------------------------------

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input form-select-inline'}),
        }


# ---------------------------------------------------------------------------
# Dashboard: update reservation status
# ---------------------------------------------------------------------------

class ReservationStatusForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input form-select-inline'}),
        }
