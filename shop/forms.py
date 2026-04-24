from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Order


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='ایمیل')
    first_name = forms.CharField(max_length=100, required=True, label='نام')
    last_name = forms.CharField(max_length=100, required=True, label='نام خانوادگی')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        labels = {
            'username': 'نام کاربری',
            'password1': 'رمز عبور',
            'password2': 'تکرار رمز عبور',
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='نام کاربری')
    password = forms.CharField(label='رمز عبور', widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'postal_code', 'avatar']
        labels = {
            'phone': 'شماره تلفن',
            'address': 'آدرس',
            'city': 'شهر',
            'postal_code': 'کد پستی',
            'avatar': 'عکس پروفایل',
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'postal_code', 'notes']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'phone': 'شماره تلفن',
            'address': 'آدرس',
            'city': 'شهر',
            'postal_code': 'کد پستی',
            'notes': 'توضیحات (اختیاری)',
        }
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
