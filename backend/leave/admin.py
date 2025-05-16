from django.contrib import admin
from .models import LeaveBalance, LeaveComment, LeavePolicy, LeaveRequest, LeaveType, Holiday
# Register your models here.


admin.site.register(LeaveType)
admin.site.register(LeaveBalance)
admin.site.register(LeaveComment)
admin.site.register(LeaveRequest)
admin.site.register(LeavePolicy)
admin.site.register(Holiday)
