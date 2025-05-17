from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages

from .models import JobQuestion, ApplicantAnswer
from jobapp.models import Job, Applicant
from jobapp.permission import user_is_employer, user_is_employee
from .utils import generate_questions_for_job, test_gemini_api
from whisper_vid_audio.transcribe import WhisperTranscriber

def test_question_generation(request):
    """Test the question generation functionality"""
    if not request.user.is_superuser:
        return HttpResponse("Access denied. Only superusers can run this test.")
    
    api_working = test_gemini_api()
    
    response_data = {
        "api_test": "Success" if api_working else "Failed",
    }
    
    # If the API is working, try generating questions for a job
    if api_working:
        try:
            # Get a job to test with
            job = Job.objects.filter(is_published=True).first()
            
            if job:
                # Clear existing questions
                JobQuestion.objects.filter(job=job).delete()
                
                # Generate new questions
                questions = generate_questions_for_job(job)
                
                # Add results to response
                response_data["job_title"] = job.title
                response_data["questions_generated"] = questions.count()
                response_data["sample_questions"] = [q.question_text for q in questions[:3]]
            else:
                response_data["job_test"] = "No published jobs found to test with"
        except Exception as e:
            response_data["job_test_error"] = str(e)
    
    return JsonResponse(response_data)

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def generate_job_questions(request, job_id):
    """Generate questions for a specific job"""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    
    # Generate questions
    questions = generate_questions_for_job(job)
    
    messages.success(request, f'Successfully generated {questions.count()} questions for "{job.title}"')
    return redirect('jobapp:single-job', id=job_id)

@login_required(login_url=reverse_lazy('account:login'))
def view_job_questions(request, job_id):
    """View questions for a specific job"""
    job = get_object_or_404(Job, id=job_id)
    
    # If no questions exist, generate them for employers
    questions = JobQuestion.objects.filter(job=job)
    if not questions.exists() and request.user.id == job.user.id:
        questions = generate_questions_for_job(job)
    
    # Get general and skill-specific questions
    general_questions = questions.filter(is_general=True)
    skill_questions = questions.filter(is_general=False)
    
    # Group skill questions by skill
    skills_dict = {}
    for question in skill_questions:
        skill = question.skill_related or "Other"
        if skill not in skills_dict:
            skills_dict[skill] = []
        skills_dict[skill].append(question)
    
    context = {
        'job': job,
        'general_questions': general_questions,
        'skills_dict': skills_dict,
        'total_questions': questions.count()
    }
    
    return render(request, 'question_generation/view_questions.html', context)

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def answer_job_questions(request, job_id):
    """Answer questions for a job application"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if the user has applied for this job
    try:
        applicant = Applicant.objects.get(user=request.user, job=job)
    except Applicant.DoesNotExist:
        messages.error(request, 'You must apply for this job before answering questions.')
        return redirect('jobapp:single-job', id=job_id)
    
    # Get questions for this job
    questions = JobQuestion.objects.filter(job=job)
    
    # If no questions exist, generate them
    if not questions.exists():
        questions = generate_questions_for_job(job)
    
    # Check if all questions have been answered
    answered_questions = ApplicantAnswer.objects.filter(applicant=applicant).values_list('question_id', flat=True)
    unanswered_questions = questions.exclude(id__in=answered_questions)
    
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        audio_file = request.FILES.get('audio_file')
        
        if not question_id or not audio_file:
            messages.error(request, 'Question ID and audio file are required.')
            return redirect('question_generation:answer_job_questions', job_id=job_id)
        
        # Get the question
        question = get_object_or_404(JobQuestion, id=question_id, job=job)
        
        # Create a new answer
        answer = ApplicantAnswer(
            applicant=applicant,
            question=question,
            audio_file=audio_file
        )
        answer.save()
        
        # Transcribe the audio file
        try:
            transcriber = WhisperTranscriber()
            result = transcriber.transcribe(answer.audio_file.path)
            transcription = result.get('text', '')
            
            # Save the transcription
            answer.answer_text = transcription
            answer.transcription = transcription
            answer.save()
            
            messages.success(request, 'Your answer has been recorded and transcribed.')
        except Exception as e:
            messages.error(request, f'Error during transcription: {str(e)}')
        
        # Redirect to the same page to continue answering questions
        return redirect('question_generation:answer_job_questions', job_id=job_id)
    
    context = {
        'job': job,
        'applicant': applicant,
        'questions': questions,
        'unanswered_questions': unanswered_questions,
        'answered_count': len(answered_questions),
        'total_count': questions.count()
    }
    
    return render(request, 'question_generation/answer_questions.html', context)

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def view_applicant_answers(request, applicant_id, job_id):
    """View an applicant's answers to job questions"""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    applicant = get_object_or_404(Applicant, id=applicant_id, job=job)
    
    # Get questions and answers
    questions = JobQuestion.objects.filter(job=job)
    answers = ApplicantAnswer.objects.filter(applicant=applicant)
    
    # Create a dictionary of answers keyed by question
    answers_dict = {answer.question_id: answer for answer in answers}
    
    # Prepare data for template
    questions_with_answers = []
    for question in questions:
        questions_with_answers.append({
            'question': question,
            'answer': answers_dict.get(question.id)
        })
    
    context = {
        'job': job,
        'applicant': applicant,
        'questions_with_answers': questions_with_answers,
        'answered_count': answers.count(),
        'total_count': questions.count()
    }
    
    return render(request, 'question_generation/view_answers.html', context)
