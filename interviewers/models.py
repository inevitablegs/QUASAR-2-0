from django.db import models
from django.contrib.auth.models import User
import uuid

from django.db import models
from django.contrib.auth.models import User

class InterviewerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, default="InsightHire")  # Added field
    zoom_account_id = models.CharField(max_length=255, blank=True, null=True)
    zoom_client_id = models.CharField(max_length=255, blank=True, null=True)
    zoom_client_secret = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.company_name})"

    

class InterviewRecording(models.Model):
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate_name = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to="interview_audio/")
    transcribed_text = models.TextField(blank=True, null=True)
    evaluation_report = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_name} - {self.interviewer.username}"
    
class InterviewerVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_verified = models.BooleanField(default=False)