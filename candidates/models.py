# candidates/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)  # New field
    github_profile = models.URLField(blank=True, null=True)  # New field
    address = models.TextField(blank=True, null=True)  # New field
    skills = models.CharField(max_length=500, blank=True, null=True)  # New field
    experience = models.CharField(max_length=255, blank=True, null=True)  # New field
    company_applied = models.CharField(max_length=255, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    audio_file = models.FileField(upload_to="interview_audio/", blank=True, null=True)
    video_file = models.FileField(upload_to="interview_videos/", blank=True, null=True)
    emotion_analysis = models.TextField(blank=True, null=True)
    overall_report = models.TextField(blank=True, null=True)
    hiring_recommendation = models.FloatField(blank=True, null=True)
    application_status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    def __str__(self):
        return self.user.username
    

class CandidateVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_verified = models.BooleanField(default=False)