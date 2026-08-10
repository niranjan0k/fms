from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("levels/", views.level_list, name="level_list"),
    path("levels/new/", views.level_create, name="level_create"),
    path("levels/<int:pk>/edit/", views.level_edit, name="level_edit"),
    path("levels/<int:pk>/delete/", views.level_delete, name="level_delete"),
    path("role-rights/", views.role_rights, name="role_rights"),
]
