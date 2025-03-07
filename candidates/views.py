from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ResumeUploadForm, CandidateSignUpForm
from .models import CandidateProfile,CandidateVerification
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.http import FileResponse, Http404
import os
from django.conf import settings
from django.shortcuts import get_object_or_404

from django.contrib.auth import login
from home.models import UserProfile


from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse



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





def candidate_signup(request):
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # ✅ Deactivate account until email is verified
            user.save()

            # ✅ Create UserProfile with candidate role
            UserProfile.objects.create(user=user, role='candidate')

            # ✅ Create verification token
            verification = CandidateVerification.objects.create(user=user)

            # ✅ Send verification email
            current_site = get_current_site(request)
            verification_link = f"http://{current_site.domain}{reverse('candidate_verify_email', kwargs={'token': verification.token})}"
            subject = "Verify Your Email - InsightHire"
            message = render_to_string('candidates/email_verification.html', {
                'verification_link': verification_link,
                'user': user
            })

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            email.content_subtype = "html"
            email.send()

            # ✅ Show instruction message to check email
            return render(request, 'candidates/verify_instruction.html')

    else:
        form = CandidateSignUpForm()

    return render(request, 'candidates/signup.html', {'form': form})



def candidate_verify_email(request, token):
    try:
        verification = CandidateVerification.objects.get(token=token)
        verification.is_verified = True
        verification.save()

        # Activate the user
        verification.user.is_active = True
        verification.user.save()

        # Use `reverse` to get the correct path for 'candidate_login'
        login_url = reverse('candidate_login')  # This generates '/candidate/login/'

        return HttpResponse(f"Email verified successfully! You can now <a href='{login_url}'>login</a>.")
        
    except CandidateVerification.DoesNotExist:
        return HttpResponse("Invalid verification link.")