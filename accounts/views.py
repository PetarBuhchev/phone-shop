from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm
import logging

logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.username}")
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            logger.info(f"User {request.user.username} updated their profile")
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        try:
            profile_form = UserProfileForm(instance=request.user.userprofile)
        except:
            from .models import UserProfile
            UserProfile.objects.create(user=request.user)
            profile_form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def logout_view(request):
    logger.info(f"User {request.user.username} logged out")
    logout(request)
    return redirect('shop:product_list')

