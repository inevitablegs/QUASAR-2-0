from django.urls import path
from .views import home
from .views import interviewer_view, candidate_view, privacy_policy_view, terms_of_service_view, contact_us_view, not_found_view

urlpatterns = [
    path('', home, name='home'),  # Home page route
    path('interviewers/', interviewer_view, name='interviewer'),
    path('candidates/', candidate_view, name='candidate'),
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_of_service_view, name='terms_of_service'),
    path('contact/', contact_us_view, name='contact_us'),
    path('notfound/', not_found_view, name='not_Found'),
]


