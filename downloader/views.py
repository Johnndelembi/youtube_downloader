from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import DownloadForm, UserRegisterForm
import yt_dlp
import os
import subprocess
from django.conf import settings
import time

class ProgressHandler:
    def __init__(self, request):
        self.request = request
        self.start_time = time.time()
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    progress = (downloaded / total) * 100
                    speed = d.get('speed', 0)
                    if speed:
                        speed = speed / 1024 / 1024  # Convert to MB/s
                        eta = d.get('eta', 0)
                        
                        # Store progress in session
                        self.request.session['download_progress'] = {
                            'progress': round(progress, 1),
                            'speed': round(speed, 2),
                            'eta': eta
                        }
                        self.request.session.modified = True
                        
            except Exception as e:
                print(f"Progress calculation error: {str(e)}")

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

class CustomLoginView(LoginView):
    template_name = 'downloader/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')

class CustomLogoutView(LogoutView):
    template_name = 'downloader/logout.html'
    next_page = 'home'

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
    if request.method == 'POST':
        form = DownloadForm(request.POST)
        if form.is_valid():
            print("Form is valid, starting download process...")  # Debug print
            
            # Check for FFmpeg first
            if not check_ffmpeg():
                messages.error(request, 'FFmpeg is not installed. Please install FFmpeg to download videos.')
                return redirect('home')

            url = form.cleaned_data['url']
            download_format = form.cleaned_data['format']
            quality = form.cleaned_data.get('quality', 'highest')
            
            print(f"Download request - URL: {url}, Format: {download_format}, Quality: {quality}")  # Debug print
            
            try:
                # Create downloads directory
                download_path = os.path.join(settings.MEDIA_ROOT, 'downloads')
                os.makedirs(download_path, exist_ok=True)
                print(f"Download path: {download_path}")  # Debug print

                # Initialize progress handler
                progress_handler = ProgressHandler(request)

                # Base yt-dlp options
                ydl_opts = {
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_handler.progress_hook],
                    'verbose': True,  # Add verbose output
                }

                if download_format == 'mp4':
                    print("Configuring video download options...")  # Debug print
                    if quality == 'highest':
                        format_spec = 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
                    else:
                        height = quality.replace('p', '')
                        format_spec = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    
                    ydl_opts.update({
                        'format': format_spec,
                        'merge_output_format': 'mp4',
                    })
                
                elif download_format == 'mp3':
                    print("Configuring audio download options...")  # Debug print
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    })

                print(f"Final yt-dlp options: {ydl_opts}")  # Debug print

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        print("Starting download with yt-dlp...")  # Debug print
                        info = ydl.extract_info(url, download=True)
                        
                        if info:
                            video_title = info.get('title', 'Unknown Title')
                            print(f"Download completed: {video_title}")  # Debug print
                            
                            # Check if file exists
                            expected_file = os.path.join(
                                download_path, 
                                f"{video_title}.{download_format}"
                            )
                            if os.path.exists(expected_file):
                                print(f"File exists at: {expected_file}")  # Debug print
                                messages.success(
                                    request, 
                                    f'Successfully downloaded: {video_title} ({download_format.upper()})'
                                )
                            else:
                                print(f"File not found at: {expected_file}")  # Debug print
                                raise Exception("Downloaded file not found")
                        else:
                            raise Exception("Failed to get video information")

                except yt_dlp.utils.DownloadError as e:
                    print(f"yt-dlp Download Error: {str(e)}")  # Debug print
                    messages.error(request, f'Download Error: {str(e)}')
                except Exception as e:
                    print(f"Download Process Error: {str(e)}")  # Debug print
                    messages.error(request, f'Download Process Error: {str(e)}')

            except Exception as e:
                print(f"Setup Error: {str(e)}")  # Debug print
                messages.error(request, f'Setup Error: {str(e)}')
            
            if 'download_progress' in request.session:
                del request.session['download_progress']
            
            return redirect('home')
        else:
            print(f"Form errors: {form.errors}")  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DownloadForm()
    
    ffmpeg_installed = check_ffmpeg()
    if not ffmpeg_installed:
        print("FFmpeg not installed!")  # Debug print
        messages.warning(request, 'FFmpeg is not installed. Some features may not work properly.')
    
    return render(request, 'downloader/home.html', {
        'form': form,
        'ffmpeg_installed': ffmpeg_installed
    })

def get_progress(request):
    """AJAX endpoint to get download progress"""
    progress_data = request.session.get('download_progress', {
        'progress': 0,
        'speed': 0,
        'eta': 0
    })
    return JsonResponse(progress_data)

