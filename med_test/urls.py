from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tests import views as tests_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', tests_views.index, name='index'),
    path('accounts/', include('accounts.urls')),
    path('tests/', include('tests.urls')),
    path('administration/', include('administration.urls')),  # ВСЁ через administration
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)