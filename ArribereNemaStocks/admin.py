from django.contrib import admin

# Register your models here.
from .models import Strain, Tube, Box, FreezeGroup

admin.site.register(Strain)
admin.site.register(Tube)
admin.site.register(Box)
admin.site.register(FreezeGroup)


