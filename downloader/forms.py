from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class DownloadForm(forms.Form):
    url = forms.URLField(
        widget=forms.URLInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Paste YouTube URL here...'
            }
        )
    )
    format = forms.ChoiceField(
        choices=[('mp4', 'MP4 (Video)'), ('mp3', 'MP3 (Audio)')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quality = forms.ChoiceField(
        choices=[
            ('highest', 'Best Quality'),
            ('1080p', '1080p'),
            ('720p', '720p'),
            ('480p', '480p'),
            ('360p', '360p')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].label = fieldname.capitalize()
