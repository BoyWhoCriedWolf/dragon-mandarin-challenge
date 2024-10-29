from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('mainapp.urls')),
    path('admin/', admin.site.urls),

    path('api-auth/', include('rest_framework.urls'))
]

if settings.ENVIRONMENT == 'dev':
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ModuleNotFoundError:
        pass
