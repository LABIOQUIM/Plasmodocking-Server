from django.contrib import admin
from .models import Arquivos_virtaulS, Macromoleculas_virtaulS, UserCustom

# Register your models here.
admin.site.register(Arquivos_virtaulS)
admin.site.register(Macromoleculas_virtaulS)
admin.site.register(UserCustom)