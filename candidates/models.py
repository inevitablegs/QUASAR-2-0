# candidates/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    company_applied = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    meeting_link = models.URLField(blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    audio_file = models.FileField(upload_to="interview_audio/", blank=True, null=True)
    video_file = models.FileField(upload_to="interview_videos/", blank=True, null=True)
    emotion_analysis = models.TextField(blank=True, null=True)
    overall_report = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username
    

class CandidateVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_verified = models.BooleanField(default=False)