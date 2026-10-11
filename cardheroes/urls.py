from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import include, path


def healthz(request):
    """Lightweight endpoint Render pings to know the app is alive."""
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('healthz/', healthz, name='healthz'),
    path(settings.ADMIN_URL, admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),   # provides the set_language view
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('', include('shop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
