from django.contrib import admin
from wholesaleApp.models.supplier import (SupplierMaster)
from wholesaleApp.models.customers import (AreaMaster, CustomerMaster,SubareaMaster)

# Register your models here.

admin.site.register(SupplierMaster)
admin.site.register(AreaMaster)
admin.site.register(CustomerMaster)
admin.site.register(SubareaMaster)