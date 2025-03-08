from django.urls import path, re_path
from django.views.static import serve
from .views import InterviewerLoginView, interviewer_dashboard, interviewer_signup, interviewer_analysis, interviewer_profile, view_candidate_profile,verify_email 
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login/', InterviewerLoginView.as_view(), name='interviewer_login'),
    path('signup/', interviewer_signup, name='interviewer_signup'),
    path('dashboard/', interviewer_dashboard, name='interviewer_dashboard'),
    path('analysis/', interviewer_analysis, name='interviewer_analysis'),
    path('verify/<uuid:token>/', verify_email, name='verify_email'),
    path('profile/', interviewer_profile, name='interviewer_profile'),
    path('candidate/<int:candidate_id>/', view_candidate_profile, name='view_candidate_profile'),
    re_path(r'^interviewer/resumes/(?P<path>.*)$', serve, {'document_root': settings.RESUME_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
