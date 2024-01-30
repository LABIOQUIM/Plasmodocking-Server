from django.contrib import admin
from .models import Arquivos_virtaulS, Macromoleculas_virtaulS, UserCustom, Macro_Prepare

# Register your models here.
admin.site.register(Arquivos_virtaulS)
admin.site.register(Macromoleculas_virtaulS)
admin.site.register(UserCustom)
admin.site.register(Macro_Prepare)