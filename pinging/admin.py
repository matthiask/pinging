from django.contrib import admin

from pinging import models


admin.site.register(models.PingServer)
admin.site.register(
    models.PingedURL,
    list_display=('created', 'server', 'weblogurl', 'status', 'message'),
    list_filter=('server', 'status'),
)
