from django.contrib import admin
from sc_app.models import Info, Closed, Movement, Colors, Cbgs, CbgStore

# Register your models here.
admin.site.register(Info)
admin.site.register(Closed)
admin.site.register(Movement)
admin.site.register(Colors)
admin.site.register(Cbgs)
admin.site.register(CbgStore)
