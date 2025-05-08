from django.contrib import admin
from .models import Employee, EmployeeDocument, EmployeeEducation, EmployeeExperience, EmployeeSkill, EmployeeTimeline, Department, Designation

# Register your models here.

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "date_of_birth"]

admin.site.register(Employee,EmployeeAdmin)
admin.site.register(EmployeeDocument)
admin.site.register(EmployeeEducation)
admin.site.register(EmployeeExperience)
admin.site.register(EmployeeSkill)
admin.site.register(EmployeeTimeline)
admin.site.register(Department)
admin.site.register(Designation)