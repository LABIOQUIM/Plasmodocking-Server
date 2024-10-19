from django.contrib import admin
from .models import MacromoleculesFalciparumWithRedocking, ProcessPlasmodocking, UserCustom, MacroPrepare, MacromoleculesFalciparumWithoutRedocking, MacromoleculesVivaxWithRedocking

from import_export.admin import ImportExportModelAdmin


from import_export import resources

@admin.register(MacromoleculesFalciparumWithRedocking)
class MacromoleculesFalciparumWithRedockingAdmin(ImportExportModelAdmin):
    pass

@admin.register(MacromoleculesFalciparumWithoutRedocking)
class MacromoleculesFalciparumWithoutRedockingAdmin(ImportExportModelAdmin):
    pass

@admin.register(MacromoleculesVivaxWithRedocking)
class MacromoleculesVivaxWithRedockingAdmin(ImportExportModelAdmin):
    pass

@admin.register(ProcessPlasmodocking)
class ProcessPlasmodockingAdmin(ImportExportModelAdmin):
    pass
        
@admin.register(UserCustom)
class UserCustomAdmin(ImportExportModelAdmin):
    pass

# Register your models here.
admin.site.register(MacroPrepare)