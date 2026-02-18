from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Custom login view that handles pending cart additions.
    After successful login, user is redirected to complete pending cart operations.
    """
    template_name = 'accounts/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if there's a pending cart addition
        if 'pending_cart_add' in self.request.session:
            context['pending_cart_message'] = True
        return context
    
    def get_success_url(self):
        """
        Redirect to complete pending cart addition if exists, otherwise use next parameter.
        """
        # Check if there's a pending cart addition to complete
        if 'pending_cart_add' in self.request.session:
            return '/cart/complete-pending/'
        
        # Otherwise use the default next parameter
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        
        return super().get_success_url()


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.username}")
            login(request, user)
            
            # Check for pending cart addition after registration
            if 'pending_cart_add' in request.session:
                return redirect('cart:complete_pending_add')
            
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
