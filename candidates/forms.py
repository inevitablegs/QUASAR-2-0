from django import forms
from .models import CandidateProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['resume', 'job_title']  # Added job_title field

        widgets = {
            'resume': forms.ClearableFileInput(attrs={'required': False}),  # Optional field
        }

class CandidateSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['resume', 'linkedin_profile', 'github_profile', 'address', 'skills', 'experience']