from django.urls import path
from . import views

urlpatterns = [
    path("", views.letter_list, name="letter_list"),
    path("inbox/", views.letter_inbox, name="letter_inbox"),
    path("new/", views.letter_create, name="letter_create"),
    path("reports/", views.reports, name="reports"),
    path("<uuid:pk>/", views.letter_detail, name="letter_detail"),
    path("<uuid:pk>/forward/", views.letter_forward, name="letter_forward"),
    path("<uuid:pk>/complete/", views.letter_complete, name="letter_complete"),
    path("<uuid:pk>/comment/", views.letter_comment, name="letter_comment"),
]
