# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import login
from .forms import RegisterForm

from accounts.forms import EditProfileForm

@login_required
def profile(request):
    return render(request, 'profile.html')

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        # 1. Next URL
        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        # 2. Staff redirect
        if self.request.user.is_staff:
            return reverse_lazy("dashboard:home")

        # 3. Default
        return reverse_lazy("profile")

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('profile')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})