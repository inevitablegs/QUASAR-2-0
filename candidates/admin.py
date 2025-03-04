from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CandidateProfile

class CandidateProfileAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

admin.site.register(CandidateProfile, CandidateProfileAdmin)

