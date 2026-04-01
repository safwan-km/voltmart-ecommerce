from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={'class': 'form-control input', 'placeholder': 'Email'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control input', 'placeholder': 'Username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control input', 'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control input', 'placeholder': 'Confirm Password'}),
        }