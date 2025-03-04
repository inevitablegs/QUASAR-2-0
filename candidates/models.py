# candidates/models.py
from django.db import models
from django.contrib.auth.models import User

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)  # Job title field
    audio_file = models.FileField(upload_to="interview_audio/", blank=True, null=True)  # ✅ Added this field
    video_file = models.FileField(upload_to="interview_videos/", blank=True, null=True)

    def __str__(self):
        return self.user.username
