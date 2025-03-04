from django.shortcuts import render

def home(request):
    return render(request, 'home/index.html')

def interviewer_view(request):
    return render(request, 'home/interviewer.html')

def candidate_view(request):
    return render(request, 'home/candidate.html')

def privacy_policy_view(request):
    return render(request, 'home/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'home/terms_of_service.html')

def contact_us_view(request):
    return render(request, 'home/contact_us.html')

def not_found_view(request):
    return render(request, 'home/not_Found.html')


