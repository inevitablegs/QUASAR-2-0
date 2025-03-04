from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from candidates.models import CandidateProfile
from home.models import UserProfile
from .models import InterviewerProfile, InterviewRecording
from .forms import InterviewerSignUpForm
from .utils import generate_interview_questions, schedule_meeting, transcribe_audio, generate_heatmap, analyze_video_emotions, generate_interview_analysis, generate_overall_report

import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class InterviewerLoginView(LoginView):
    template_name = 'interviewers/login.html'

    def form_valid(self, form):
        user = form.get_user()
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role != 'interviewer' or user.is_superuser:
                return redirect('home')  # Prevent admin login to interviewer dashboard
        except UserProfile.DoesNotExist:
            return redirect('home')
        login(self.request, user)
        return redirect('interviewer_dashboard')




def interviewer_signup(request):
    if request.method == 'POST':
        form = InterviewerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # ✅ Ensure UserProfile is created
            UserProfile.objects.get_or_create(user=user, defaults={"role": "interviewer"})

            # ✅ Save Zoom credentials in InterviewerProfile
            interviewer_profile, created = InterviewerProfile.objects.get_or_create(user=user)
            interviewer_profile.zoom_account_id = form.cleaned_data['zoom_account_id']
            interviewer_profile.zoom_client_id = form.cleaned_data['zoom_client_id']
            interviewer_profile.zoom_client_secret = form.cleaned_data['zoom_client_secret']
            interviewer_profile.save()  # ✅ Save the profile with credentials

            return redirect('interviewer_dashboard')
    else:
        form = InterviewerSignUpForm()
    
    return render(request, 'interviewers/signup.html', {'form': form})




@login_required
def interviewer_dashboard(request):
    resumes = CandidateProfile.objects.exclude(resume__isnull=True).exclude(resume__exact='')
    questions = None
    meeting_link = None
    evaluation_reports = {}

    interviewer_profile, created = InterviewerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        candidate = CandidateProfile.objects.get(id=resume_id)

        if 'generate_questions' in request.POST:
            # Generate questions for the specific candidate
            questions = generate_interview_questions(candidate.resume.path)
            # Store the questions in the context with the candidate's ID
            questions = {resume_id: questions}

        elif 'schedule_meeting' in request.POST:
            start_time = request.POST.get('start_time')

            print(f"Zoom Account ID: {interviewer_profile.zoom_account_id}")
            print(f"Zoom Client ID: {interviewer_profile.zoom_client_id}")
            print(f"Zoom Client Secret: {interviewer_profile.zoom_client_secret}")

            new_meeting_link = schedule_meeting(
                topic=f"Interview with {candidate.user.username}",
                start_time=start_time,
                zoom_account_id=interviewer_profile.zoom_account_id,
                zoom_client_id=interviewer_profile.zoom_client_id,
                zoom_client_secret=interviewer_profile.zoom_client_secret
            )

            print(f"Generated meeting link: {new_meeting_link}")

            if new_meeting_link:
                candidate.meeting_link = new_meeting_link
                candidate.save()
                meeting_link = new_meeting_link


        elif 'process_audio' in request.POST and 'audio_file' in request.FILES:
            audio_file = request.FILES['audio_file']

            # Save the uploaded file temporarily
            audio_path = f"media/uploads/{audio_file.name}"
            path = default_storage.save(audio_path, ContentFile(audio_file.read()))

            # Transcribe the audio using the saved file path
            evaluation_reports[resume_id] = transcribe_audio(default_storage.path(path))

            # Optionally, delete the file after processing (uncomment to enable cleanup)
            # default_storage.delete(path)

    return render(request, 'interviewers/dashboard.html', {
        'resumes': resumes,
        'questions': questions,
        'meeting_link': meeting_link,
        'evaluation_reports': evaluation_reports
    })


@login_required
def interviewer_analysis(request):
    resume_id = request.GET.get('resume_id')  # Get the candidate ID from the request

    if not resume_id:
        return redirect('interviewer_dashboard')  # Redirect back if no candidate is selected

    candidate = get_object_or_404(CandidateProfile, id=resume_id)
    heatmap_path = None  # Initialize heatmap_path

    # ✅ Load stored emotion analysis if available
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
                emotion_results = analyze_video_emotions(candidate.video_file.path)
                emotion_analysis = generate_interview_analysis(emotion_results)  # Generate structured analysis
            
                # ✅ Save emotion analysis persistently
                candidate.emotion_analysis = emotion_analysis
                candidate.save()

        # ✅ Generate Overall Report
        elif 'generate_overall_report' in request.POST:
            if candidate.audio_file and candidate.video_file:
                # ✅ Fetch the latest stored audio analysis
                if InterviewRecording.objects.filter(candidate_name=candidate.user.username).exists():
                    audio_analysis = InterviewRecording.objects.filter(candidate_name=candidate.user.username).latest('id').transcribed_text
                else:
                    audio_analysis = "No audio analysis available."

                # ✅ Use stored emotion analysis if available
                emotion_analysis = candidate.emotion_analysis if candidate.emotion_analysis else "No emotion analysis available."

                # ✅ Generate the overall report
                overall_report = generate_overall_report(audio_analysis, emotion_analysis)

                # ✅ Save the overall report persistently
                candidate.overall_report = overall_report
                candidate.save()

    # ✅ Fetch analysis results for the selected candidate only
    recordings = InterviewRecording.objects.filter(candidate_name=candidate.user.username)

    return render(request, 'interviewers/analysis.html', {
        'candidate': candidate,
        'recordings': recordings,
        'heatmap_path': heatmap_path if 'heatmap_path' in locals() else None,  # Pass heatmap if available
        'emotion_analysis': emotion_analysis  # Pass stored emotion analysis
    })
