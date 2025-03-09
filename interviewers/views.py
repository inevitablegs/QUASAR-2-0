from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from candidates.models import CandidateProfile
from home.models import UserProfile
from .models import InterviewerProfile, InterviewRecording, InterviewerVerification
from .forms import InterviewerSignUpForm, InterviewerProfileForm
from .utils import generate_interview_questions, schedule_meeting, transcribe_audio, generate_heatmap, analyze_video_emotions, generate_interview_analysis, generate_overall_report, send_candidate_email, send_interviewer_email
from django.urls import reverse_lazy


import re
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from django.http import HttpResponse

class InterviewerLoginView(LoginView):
    template_name = 'interviewers/login.html'

    def form_valid(self, form):
        user = form.get_user()
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role != 'interviewer' or user.is_superuser:
                # Prevent admin login to interviewer dashboard
                return redirect('home')
        except UserProfile.DoesNotExist:
            return redirect('home')
        login(self.request, user)
        return redirect('interviewer_dashboard')


# interviewers/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import InterviewerSignUpForm
from home.models import UserProfile

def interviewer_signup(request):
    if request.method == 'POST':
        form = InterviewerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email is verified
            user.save()

            # Ensure UserProfile is created
            UserProfile.objects.get_or_create(
                user=user, defaults={"role": "interviewer"})

            # Save Zoom credentials and company name in InterviewerProfile
            interviewer_profile, created = InterviewerProfile.objects.get_or_create(
                user=user)
            interviewer_profile.company_name = form.cleaned_data['company_name']
            interviewer_profile.zoom_account_id = form.cleaned_data['zoom_account_id']
            interviewer_profile.zoom_client_id = form.cleaned_data['zoom_client_id']
            interviewer_profile.zoom_client_secret = form.cleaned_data['zoom_client_secret']
            interviewer_profile.save()  # ✅ Save the profile with credentials

            # ✅ Create verification token
            verification = InterviewerVerification.objects.create(user=user)

            # ✅ Send verification email
            current_site = get_current_site(request)
            verification_link = f"http://{current_site.domain}{reverse('verify_email', kwargs={'token': verification.token})}"
            subject = "Verify Your Email - InsightHire"
            message = render_to_string('interviewers/email_verification.html', {
                                       'verification_link': verification_link, 'user': user})

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            email.content_subtype = "html"  # This is the key to sending HTML email
            email.send()

            # Show message to check email
            return render(request, 'interviewers/verify_instruction.html')

    else:
        form = InterviewerSignUpForm()

    return render(request, 'interviewers/signup.html', {'form': form})



def verify_email(request, token):
    try:
        verification = InterviewerVerification.objects.get(token=token)
        verification.is_verified = True
        verification.save()

        # Activate the user
        verification.user.is_active = True
        verification.user.save()

        # Use `reverse` to get the correct path for 'interviewer_login'
        login_url = reverse('interviewer_login')  # This generates '/interviewer/login/'

        return HttpResponse(f"Email verified successfully! You can now <a href='{login_url}'>login</a>.")
        
    except InterviewerVerification.DoesNotExist:
        return HttpResponse("Invalid verification link.")
    
@login_required
def view_candidate_profile(request, candidate_id):
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)
    return render(request, 'interviewers/candidate_profile.html', {'candidate': candidate})


@login_required
def interviewer_profile(request):
    interviewer_profile, _ = InterviewerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = InterviewerProfileForm(request.POST, instance=interviewer_profile)
        if form.is_valid():
            form.save()
            return redirect('interviewer_profile')
    else:
        form = InterviewerProfileForm(instance=interviewer_profile)

    return render(request, 'interviewers/profile.html', {'form': form, 'interviewer_profile': interviewer_profile})

@login_required
def interviewer_dashboard(request):
    resumes = CandidateProfile.objects.exclude(
        resume__isnull=True).exclude(resume__exact='')
    questions = None
    meeting_link = None
    evaluation_reports = {}

    interviewer_profile = InterviewerProfile.objects.get(user=request.user)
    candidates = CandidateProfile.objects.filter(company_applied=interviewer_profile.company_name)

    interviewer_profile = InterviewerProfile.objects.get(user=request.user)
    candidates = CandidateProfile.objects.filter(company_applied=interviewer_profile.company_name)

    interviewer_profile, created = InterviewerProfile.objects.get_or_create(
        user=request.user)

    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        if not resume_id:
            # Handle the case where resume_id is missing or empty
            return HttpResponse("Resume ID is missing.", status=400)
        
        try:
            candidate = CandidateProfile.objects.get(id=resume_id)
        except CandidateProfile.DoesNotExist:
            return HttpResponse("Candidate not found.", status=404)

        if 'generate_questions' in request.POST:
           # Generate questions for the specific candidate
            questions = generate_interview_questions(candidate.resume.path)
            # Store the questions in the context with the candidate's ID
            questions = {resume_id: questions}

        elif 'schedule_meeting' in request.POST:
            start_time = request.POST.get('start_time')

            new_meeting_link = schedule_meeting(
                topic=f"Interview with {candidate.user.username}",
                start_time=start_time,
                zoom_account_id=interviewer_profile.zoom_account_id,
                zoom_client_id=interviewer_profile.zoom_client_id,
                zoom_client_secret=interviewer_profile.zoom_client_secret
            )

            if new_meeting_link:
                candidate.meeting_link = new_meeting_link
                candidate.save()

                # Send separate emails to candidate and interviewer
                send_candidate_email(
                    candidate_email=candidate.user.email,
                    candidate_name=candidate.user.username,
                    meeting_link=new_meeting_link,
                    start_time=start_time
                )

                send_interviewer_email(
                    interviewer_email=request.user.email,
                    interviewer_name=request.user.username,
                    candidate_name=candidate.user.username,
                    meeting_link=new_meeting_link,
                    start_time=start_time
                )

                meeting_link = new_meeting_link

        elif 'process_audio' in request.POST and 'audio_file' in request.FILES:
            audio_file = request.FILES['audio_file']

            # Save the uploaded file temporarily
            audio_path = f"media/uploads/{audio_file.name}"
            path = default_storage.save(
                audio_path, ContentFile(audio_file.read()))

            # Transcribe the audio using the saved file path
            evaluation_reports[resume_id] = transcribe_audio(
                default_storage.path(path))

            # Optionally, delete the file after processing (uncomment to enable cleanup)
            # default_storage.delete(path)

    return render(request, 'interviewers/dashboard.html', {
        'resumes': resumes,
        'questions': questions,
        'meeting_link': meeting_link,
        'evaluation_reports': evaluation_reports,
        'candidates': candidates
    })


@login_required
def interviewer_analysis(request):
    # Get the candidate ID from the request
    resume_id = request.GET.get('resume_id')

    if not resume_id:
        return redirect('interviewer_dashboard')

    candidate = get_object_or_404(CandidateProfile, id=resume_id)
    heatmap_path = None
    emotion_analysis = candidate.emotion_analysis if candidate.emotion_analysis else None

    if request.method == 'POST':
        # ✅ Upload Audio
        if 'upload_audio' in request.POST and 'audio_file' in request.FILES:
            audio_file = request.FILES['audio_file']
            candidate.audio_file = audio_file
            candidate.save()

        # ✅ Analyze Audio
        elif 'analyze_audio' in request.POST:
            if candidate.audio_file:
                evaluation_result = transcribe_audio(candidate.audio_file.path)

                if evaluation_result and "Error" not in evaluation_result:
                    interview_record, created = InterviewRecording.objects.get_or_create(
                        interviewer=request.user,
                        candidate_name=candidate.user.username,
                        audio_file=candidate.audio_file
                    )
                    interview_record.transcribed_text = evaluation_result
                    interview_record.save()

        # ✅ Upload Video
        elif 'upload_video' in request.POST and 'video_file' in request.FILES:
            video_file = request.FILES['video_file']
            candidate.video_file = video_file
            candidate.save()

        # ✅ Generate Heatmap
        elif 'analyze_video' in request.POST:
            if candidate.video_file:
                heatmap_path = generate_heatmap(candidate.video_file.path)

        # ✅ Analyze Video Emotions
        elif 'analyze_emotions' in request.POST:
            if candidate.video_file:
                emotion_results = analyze_video_emotions(
                    candidate.video_file.path)
                emotion_analysis = generate_interview_analysis(
                    emotion_results)  # Generate structured analysis

                # ✅ Save emotion analysis persistently
                candidate.emotion_analysis = emotion_analysis
                candidate.save()

        # ✅ Generate Overall Report
        elif 'generate_overall_report' in request.POST:
            if candidate.audio_file and candidate.video_file:
                # ✅ Fetch the latest stored audio analysis
                if InterviewRecording.objects.filter(candidate_name=candidate.user.username).exists():
                    audio_analysis = InterviewRecording.objects.filter(
                        candidate_name=candidate.user.username).latest('id').transcribed_text
                else:
                    audio_analysis = "No audio analysis available."

                # ✅ Use stored emotion analysis if available
                emotion_analysis = candidate.emotion_analysis if candidate.emotion_analysis else "No emotion analysis available."

                # ✅ Generate the overall report and save the hiring recommendation
                overall_report = generate_overall_report(audio_analysis, emotion_analysis, candidate)

                # ✅ Save the overall report persistently
                candidate.overall_report = overall_report
                candidate.save()

    # Fetch analysis results for the selected candidate only
    recordings = InterviewRecording.objects.filter(candidate_name=candidate.user.username)

    return render(request, 'interviewers/analysis.html', {
        'candidate': candidate,
        'recordings': recordings,
        'heatmap_path': heatmap_path if 'heatmap_path' in locals() else None,
        'emotion_analysis': emotion_analysis
    })



# @login_required
# def update_application_status(request, candidate_id):
#     candidate = get_object_or_404(CandidateProfile, id=candidate_id)

#     if request.method == "POST":
#         status = request.POST.get("status")
#         candidate.application_status = status
#         candidate.save()

#         # Send email notification
#         subject = "Your Interview Result - InsightHire"
#         if status == "Accepted":
#             message = f"Congratulations {candidate.user.first_name},\n\nYou have been selected for the next step in the hiring process! 🎉"
#         else:
#             message = f"Dear {candidate.user.first_name},\n\nUnfortunately, you were not selected for this position. We encourage you to apply again in the future!"

#         send_mail(
#             subject,
#             message,
#             "no-reply@insighthire.com",
#             [candidate.user.email],
#             fail_silently=False,
#         )

#     return redirect("analysis_page")


from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from candidates.models import CandidateProfile
import re

def calculate_hiring_recommendation(overall_report):
    """
    Function to calculate hiring recommendation percentage based on the overall report.
    This uses keyword detection to determine the score.
    """
    if not overall_report:
        return 0  # No report, no recommendation

    # Define weights based on keyword presence
    keywords = {
        "excellent": 90, "outstanding": 85, "strong": 80, "very good": 75,
        "good": 70, "satisfactory": 60, "average": 50, "weak": 40,
        "poor": 20, "unsatisfactory": 10
    }

    for word, score in keywords.items():
        if re.search(rf"\b{word}\b", overall_report, re.IGNORECASE):
            return score  # Assign the score based on the first keyword match

    return 50  # Default neutral recommendation if no keyword matches


@login_required
def update_application_status(request, candidate_id):
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)

    if request.method == "POST":
        status = request.POST.get("status")
        candidate.application_status = status

        # Calculate hiring recommendation from overall report
        candidate.hiring_recommendation = calculate_hiring_recommendation(candidate.overall_report)
        candidate.save()

        # Send email notification
        subject = "Your Interview Result - InsightHire"
        if status == "Accepted":
            message = f"Congratulations {candidate.user.first_name},\n\nYou have been selected for the next step in the hiring process! 🎉"
        else:
            message = f"Dear {candidate.user.first_name},\n\nUnfortunately, you were not selected for this position. We encourage you to apply again in the future!"

        send_mail(
            subject,
            message,
            "no-reply@insighthire.com",
            [candidate.user.email],
            fail_silently=False,
        )

    return redirect(reverse('analysis_page', args=[candidate_id]))


def analysis_page(request, candidate_id):
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)
    return render(request, 'interviewers/analysis.html', {'candidate': candidate})
