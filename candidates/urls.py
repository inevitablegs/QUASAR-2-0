from django.urls import path
from .views import CandidateLoginView, candidate_dashboard, candidate_signup, download_resume
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('login/', CandidateLoginView.as_view(), name='candidate_login'),
    path('signup/', candidate_signup, name='candidate_signup'),
    path('dashboard/', candidate_dashboard, name='candidate_dashboard'),
    path('logout/', LogoutView.as_view(next_page='interviewer_login'), name='interviewer_logout'),
    # path('dashboard/', candidate_dashboard, name='candidate_dashboard'),
    path('download_resume/<int:candidate_id>/', download_resume, name='download_resume'),

    
]