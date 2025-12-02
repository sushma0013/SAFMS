from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views  # project-level views like home and QR generation

urlpatterns = [
    path('admin/', admin.site.urls),

    # QR-related paths
    path('generate_qr/', views.generate_qr, name='generate_qr'),
    path('show_qr/<int:session_id>/', views.show_qr, name='show_qr'),

    # Attendance app URLs
    path('attendance/', include('attendance.urls')),  # include only app-level urls

    # Temporary home page
    path('', views.home, name='home'),
]

# Serve media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
