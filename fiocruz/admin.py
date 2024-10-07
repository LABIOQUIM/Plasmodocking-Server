from django.contrib import admin
from .models import MacromoleculesFalciparumWithRedocking, ProcessPlasmodocking, UserCustom, MacroPrepare

# Register your models here.
admin.site.register(ProcessPlasmodocking)
admin.site.register(MacromoleculesFalciparumWithRedocking)
admin.site.register(UserCustom)
admin.site.register(MacroPrepare)