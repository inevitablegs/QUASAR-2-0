from django.urls import path, re_path
from django.views.static import serve
from .views import InterviewerLoginView, interviewer_dashboard, interviewer_signup, interviewer_analysis
from django.conf import settings
from django.conf.urls.static import static
from .views import verify_email

urlpatterns = [
    path('login/', InterviewerLoginView.as_view(), name='interviewer_login'),
    path('signup/', interviewer_signup, name='interviewer_signup'),
    path('dashboard/', interviewer_dashboard, name='interviewer_dashboard'),
    path('analysis/', interviewer_analysis, name='interviewer_analysis'),
    path('verify/<uuid:token>/', verify_email, name='verify_email'),
    re_path(r'^interviewer/resumes/(?P<path>.*)$', serve, {'document_root': settings.RESUME_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
