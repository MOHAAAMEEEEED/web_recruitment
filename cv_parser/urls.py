from django.urls import path
from . import views

app_name = 'cv_parser'

urlpatterns = [
    path('upload/', views.upload_cv, name='upload_cv'),
]
