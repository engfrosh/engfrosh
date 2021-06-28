from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name=''),
    # Logins
    path("login/", views.login_page, name="login"),
    path("login/discord/", views.discord_login, name="discord_login"),
    path("login/discord/callback/", views.discord_login_callback, name="discord_login_callback"),
    path("login/failed/", views.login_failed, name="login_failed"),
    # Registrations
    path("register/", views.register_page, name="register"),
    path("register/discord/callback/", views.discord_register_callback, name="discord_register_callback"),
    path("register/discord/", views.discord_register, name="discord_register"),
    # Other
    path("welcome/discord/", views.discord_initial_setup, name="discord_welcome"),
    path("permission-denied/", views.permission_denied, name="permission_denied")
]
