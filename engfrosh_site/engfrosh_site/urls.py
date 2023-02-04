"""engfrosh_site URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
import frosh.views
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('', frosh.views.overall_index),
    path('admin/', admin.site.urls),
    path('accounts/', include('authentication.urls')),
    path('teams/', include('frosh.team_urls')),
    path('user/', include('frosh.user_urls')),
    path('manage/', include('management.urls')),
    path("scavenger/", include('scavenger.urls')),
    path("trade-up/", include("frosh.trade_up_urls")),
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("favicon.ico"))),
    path("check-in/", include('check_in.urls')),
    path("tickets/", include('ticket.urls')),
    path("api/", include('api.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
