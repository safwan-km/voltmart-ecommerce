from django.urls import path
from . import views
from django.contrib.auth.views import (
    LogoutView,
    PasswordChangeView, 
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
    )


urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    path('change-password/', PasswordChangeView.as_view(
        template_name='registration/change_password.html',
        success_url='/accounts/change-password-done/'
    ), name='change_password'),

    path('change-password-done/', PasswordChangeDoneView.as_view(
        template_name='registration/change_password_done.html'
    ), name='change_password_done'),
    
    path('password-reset/',
         PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             success_url='/accounts/password-reset/done/'
         ),
         name='password_reset'),

    path('password-reset/done/',
         PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),


    path('password-reset/',
             PasswordResetView.as_view(
                 template_name='registration/password_reset.html',
                 email_template_name='registration/password_reset_email.html',
                 success_url='/accounts/password-reset/done/'
             ),
             name='password_reset'),

    path('password-reset/done/',
         PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]

    
    
