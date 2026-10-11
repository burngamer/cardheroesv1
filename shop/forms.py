from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Card, Order


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = [
            'name', 'franchise', 'rarity', 'card_set', 'card_number',
            'condition', 'description', 'price', 'stock', 'image', 'back_image', 'featured',
        ]
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
        labels = {
            'name': _('Name'),
            'franchise': _('Franchise'),
            'rarity': _('Rarity'),
            'card_set': _('Set'),
            'card_number': _('Card number'),
            'condition': _('Condition'),
            'description': _('Description'),
            'price': _('Price'),
            'stock': _('Stock'),
            'image': _('Front image'),
            'back_image': _('Back image'),
            'featured': _('Featured on the home page'),
        }
        help_texts = {
            'card_set': _('Set / collection the card belongs to'),
            'back_image': _('The back side of the card'),
        }


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'address', 'city', 'postal_code', 'country']
        labels = {
            'full_name': _('Full name'),
            'email': _('Email'),
            'address': _('Address'),
            'city': _('City'),
            'postal_code': _('Postal code'),
            'country': _('Country'),
        }


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_('Email'))

    ROLE_CHOICES = [
        ('customer', _('Customer')),
        ('staff', _('Staff (can use the dashboard)')),
        ('superuser', _('Superuser (full control)')),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='customer', label=_('Role'))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        role = self.cleaned_data['role']
        user.is_staff = role in ('staff', 'superuser')
        user.is_superuser = role == 'superuser'
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        labels = {
            'is_active': _('Active (can log in)'),
            'is_staff': _('Staff — dashboard access'),
            'is_superuser': _('Superuser — full control'),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_('Email'))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
