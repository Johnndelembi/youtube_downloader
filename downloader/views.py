from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import UserRegisterForm, DownloadForm
import yt_dlp
import os
from django.conf import settings
import time

class CustomLoginView(LoginView):
    template_name = 'downloader/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')
    template_name = None

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'downloader/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'downloader/profile.html')

@login_required
def home(request):
    return render(request, 'downloader/home.html')

