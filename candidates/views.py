from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ResumeUploadForm, CandidateSignUpForm
from .models import CandidateProfile
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.http import FileResponse, Http404
import os
from django.conf import settings
from django.shortcuts import get_object_or_404


def download_resume(request, candidate_id):
    candidate = get_object_or_404(CandidateProfile, user_id=candidate_id)
    if candidate.resume:
        file_path = os.path.join(settings.MEDIA_ROOT, str(candidate.resume))
        try:
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
        except FileNotFoundError:
            raise Http404("Resume not found")
    else:
        raise Http404("No resume uploaded")



@login_required
def candidate_dashboard(request):
    candidate_profile, created = CandidateProfile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES, instance=candidate_profile)
        if form.is_valid():
            form.save()
            return redirect('candidate_dashboard')  # Refresh page after upload
    
    else:
        form = ResumeUploadForm(instance=candidate_profile)

    return render(request, 'candidates/dashboard.html', {
        'candidate_profile': candidate_profile,
        'form': form,  # Pass the form to the template
    })




from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from home.models import UserProfile

class CandidateLoginView(LoginView):
    template_name = 'candidates/login.html'

    def form_valid(self, form):
        user = form.get_user()
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role != 'candidate' or user.is_superuser:
                return redirect('home')  # Redirect admin users or non-candidates
        except UserProfile.DoesNotExist:
            return redirect('home')
        login(self.request, user)
        return redirect('candidate_dashboard')





from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import CandidateSignUpForm
from home.models import UserProfile

def candidate_signup(request):
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='candidate')  # Assign candidate role
            login(request, user)
            return redirect('candidate_dashboard')
    else:
        form = CandidateSignUpForm()
    return render(request, 'candidates/signup.html', {'form': form})

