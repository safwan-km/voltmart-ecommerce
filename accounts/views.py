from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy

from .forms import RegisterForm, EditProfileForm, DeleteAccountForm


@login_required
def profile(request):
    return render(request, 'profile.html')


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True  # already logged-in users skip the login page

    def get_success_url(self):
        # 1. Next URL
        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        # 2. Staff redirect
        if self.request.user.is_staff:
            return reverse_lazy("dashboard:home")

        # 3. Default
        return reverse_lazy("home")


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
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verified
            user.save()

            # Build verification email
            current_site = get_current_site(request)
            mail_subject = 'Activate your VoltMart account.'
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')

            try:
                send_mail(mail_subject, message, None, [to_email])
            except Exception:
                # Rollback: delete the inactive user so they can try again
                user.delete()
                messages.error(
                    request,
                    "We couldn't send a verification email. Please check your email address and try again."
                )
                return render(request, 'registration/register.html', {'form': form})

            return render(request, 'registration/verification_sent.html')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def activate_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'registration/activation_success.html')
    else:
        return render(request, 'registration/activation_invalid.html')


@login_required
def delete_account(request):
    user = request.user

    # Safety guard: prevent admin/staff accounts from being deleted this way
    if user.is_staff or user.is_superuser:
        messages.error(
            request,
            "Admin accounts cannot be deleted from the profile page. Use the Django admin panel."
        )
        return redirect('profile')

    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']

            # Verify the password belongs to this user
            if not user.check_password(password):
                messages.error(request, "Incorrect password. Account was not deleted.")
                return render(request, 'registration/delete_account_confirm.html', {'form': form})

            # Step 1: Anonymize all orders so sales records remain intact
            from orders.models import Order
            Order.objects.filter(user=user).update(user=None)

            # Step 2: Log user out before deleting
            logout(request)

            # Step 3: Permanently delete the user and all their personal data
            # (addresses, cart, wishlist will be cascade-deleted automatically)
            user.delete()

            messages.success(request, "Your account has been permanently deleted.")
            return redirect('home')
    else:
        form = DeleteAccountForm()

    return render(request, 'registration/delete_account_confirm.html', {'form': form})