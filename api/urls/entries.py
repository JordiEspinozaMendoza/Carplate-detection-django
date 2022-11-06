from django.urls import path
from api.views import entries as views

urlpatterns = [
    path('', views.getAllEntries),
    path('create', views.createEntry),
]
