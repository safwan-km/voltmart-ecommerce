# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def profile(request):
    return render(request, 'profile.html')
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = "registration/login.html"  
    def get_success_url(self):
        user = self.request.user

        if user.is_staff:
            return reverse_lazy("dashboard:home")
        return reverse_lazy("profile")