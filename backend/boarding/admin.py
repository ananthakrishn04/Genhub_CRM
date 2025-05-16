from django.contrib import admin
from .models import Process, ProcessTemplate, Task, TaskTemplate, Equipment, EquipmentAssignment
# Register your models here.


admin.site.register(Process)
admin.site.register(ProcessTemplate)
admin.site.register(Task)
admin.site.register(TaskTemplate)
admin.site.register(Equipment)
admin.site.register(EquipmentAssignment)