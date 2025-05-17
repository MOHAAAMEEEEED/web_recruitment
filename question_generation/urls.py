from django.urls import path
from . import views

app_name = 'question_generation'

urlpatterns = [
    path('generate/<int:job_id>/', views.generate_job_questions, name='generate_job_questions'),
    path('view/<int:job_id>/', views.view_job_questions, name='view_job_questions'),
    path('answer/<int:job_id>/', views.answer_job_questions, name='answer_job_questions'),
    path('answers/<int:applicant_id>/<int:job_id>/', views.view_applicant_answers, name='view_applicant_answers'),
    path('test/', views.test_question_generation, name='test_question_generation'),
] 