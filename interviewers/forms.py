from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InterviewerProfile
from .models import InterviewRecording


class InterviewerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=255, required=True)  # Add this line
    zoom_account_id = forms.CharField(max_length=255, required=True)
    zoom_client_id = forms.CharField(max_length=255, required=True)
    zoom_client_secret = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'zoom_account_id', 'zoom_client_id', 'zoom_client_secret']






class AudioUploadForm(forms.ModelForm):
    class Meta:
        model = InterviewRecording
        fields = ['candidate_name', 'audio_file']


class InterviewerProfileForm(forms.ModelForm):
    class Meta:
        model = InterviewerProfile
        fields = ['linkedin_profile', 'company_website', 'company_address', 'company_linkedin']