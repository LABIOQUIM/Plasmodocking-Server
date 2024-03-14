from django.contrib import admin
from .models import Process_Plasmodocking, Macromoleculas_virtaulS, UserCustom, Macro_Prepare

# Register your models here.
admin.site.register(Process_Plasmodocking)
admin.site.register(Macromoleculas_virtaulS)
admin.site.register(UserCustom)
admin.site.register(Macro_Prepare)