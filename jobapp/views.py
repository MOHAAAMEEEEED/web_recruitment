from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.serializers import serialize
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from .models import Video
from django.views.decorators.csrf import csrf_exempt
from whisper_vid_audio.transcribe import WhisperTranscriber

from account.models import User
from jobapp.forms import *
from jobapp.models import *
from jobapp.permission import *
User = get_user_model()


def home_view(request):

    published_jobs = Job.objects.filter(is_published=True).order_by('-timestamp')
    jobs = published_jobs.filter(is_closed=False)
    total_candidates = User.objects.filter(role='employee').count()
    total_companies = User.objects.filter(role='employer').count()
    paginator = Paginator(jobs, 3)
    page_number = request.GET.get('page',None)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_lists=[]
        job_objects_list = page_obj.object_list.values()
        for job_list in job_objects_list:
            job_lists.append(job_list)
        

        next_page_number = None
        if page_obj.has_next():
            next_page_number = page_obj.next_page_number()

        prev_page_number = None       
        if page_obj.has_previous():
            prev_page_number = page_obj.previous_page_number()

        data={
            'job_lists':job_lists,
            'current_page_no':page_obj.number,
            'next_page_number':next_page_number,
            'no_of_page':paginator.num_pages,
            'prev_page_number':prev_page_number
        }    
        return JsonResponse(data)
    
    context = {

    'total_candidates': total_candidates,
    'total_companies': total_companies,
    'total_jobs': len(jobs),
    'total_completed_jobs':len(published_jobs.filter(is_closed=True)),
    'page_obj': page_obj
    }
    print('ok')
    return render(request, 'jobapp/index.html', context)


from django.shortcuts import render
from .models import Category  # Assuming the model name is Category
from jobapp.models import Category

def post_job(request):
    categories = Category.objects.all()  # Fetch all categories from the database
    form = JobForm(request.POST or None)  # Assuming your form is named JobForm
    
    if request.method == 'POST' and form.is_valid():
        # Handle form submission logic here
        form.save()
    
    return render(request, 'post-job.html', {
        'form': form,
        'categories': categories,  # Pass categories to the template
    })

@cache_page(60 * 15)
def job_list_View(request):
    """

    """
    job_list = Job.objects.order_by('-timestamp')
    paginator = Paginator(job_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {

        'page_obj': page_obj,

    }
    return render(request, 'jobapp/job-list.html', context)


# @login_required(login_url=reverse_lazy('account:login'))
# @user_is_employer
# def create_job_View(request):
#     """
#     Provide the ability to create job post
#     """
#     form = JobForm(request.POST or None)

#     user = get_object_or_404(User, id=request.user.id)
#     categories = Category.objects.all()

#     if request.method == 'POST':

#         if form.is_valid():

#             instance = form.save(commit=False)
#             instance.user = user
#             # Category can be optional (None)
#             instance.save()
#             # for save tags
#             form.save_m2m()
#             messages.success(
#                     request, 'You are successfully posted your job! Please wait for review.')
#             return redirect(reverse("jobapp:single-job", kwargs={
#                                     'id': instance.id
#                                     }))

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def create_job_View(request):
    """
    Provide the ability to create job post
    """
    form = JobForm(request.POST or None)
    user = get_object_or_404(User, id=request.user.id)
    categories = Category.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = user
            instance.save()
            # for save tags
            form.save_m2m()
            messages.success(
                    request, 'You are successfully posted your job! Please wait for review.')
            return redirect(reverse("jobapp:single-job", kwargs={
                                    'id': instance.id
                                    }))

    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/post-job.html', context)


@csrf_exempt
def upload_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        new_video = Video(user=request.user, file=video_file)
        new_video.save()
        return JsonResponse({'status': 'success', 'message': 'Video uploaded successfully.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No video file provided or wrong method.'})

def single_job_view(request, id):
    """
    Provide the ability to view job details
    """
    if cache.get(id):
        job = cache.get(id)
    else:
        job = get_object_or_404(Job, id=id)
        cache.set(id,job , 60 * 15)
    related_job_list = job.tags.similar_objects()

    paginator = Paginator(related_job_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'job': job,
        'page_obj': page_obj,
        'total': len(related_job_list)

    }
    return render(request, 'jobapp/job-single.html', context)


def search_result_view(request):
    """
        User can search job with multiple fields

    """

    job_list = Job.objects.order_by('-timestamp')

    # Keywords
    if 'job_title_or_company_name' in request.GET:
        job_title_or_company_name = request.GET['job_title_or_company_name']

        if job_title_or_company_name:
            job_list = job_list.filter(title__icontains=job_title_or_company_name) | job_list.filter(
                company_name__icontains=job_title_or_company_name)

    # location
    if 'location' in request.GET:
        location = request.GET['location']
        if location:
            job_list = job_list.filter(location__icontains=location)

    # Job Type
    if 'job_type' in request.GET:
        job_type = request.GET['job_type']
        if job_type:
            job_list = job_list.filter(job_type__iexact=job_type)

    # job_title_or_company_name = request.GET.get('text')
    # location = request.GET.get('location')
    # job_type = request.GET.get('type')

    #     job_list = Job.objects.all()
    #     job_list = job_list.filter(
    #         Q(job_type__iexact=job_type) |
    #         Q(title__icontains=job_title_or_company_name) |
    #         Q(location__icontains=location)
    #     ).distinct()

    # job_list = Job.objects.filter(job_type__iexact=job_type) | Job.objects.filter(
    #     location_icontains=location) | Job.objects.filter(titleicontains=text) | Job.objects.filter(company_name_icontains=text)

    paginator = Paginator(job_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {

        'page_obj': page_obj,

    }
    return render(request, 'jobapp/result.html', context)


# Importing necessary modules
from .utils import calculate_similarity_score
from whisper_vid_audio.transcribe import WhisperTranscriber
from .models import Applicant, Job
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def apply_job_view(request, id):
    """
    Handle job application process with video upload, transcription, and similarity score calculation.
    """
    user = get_object_or_404(User, id=request.user.id)
    job = get_object_or_404(Job, id=id)

    # Check if the user has already applied for this job
    if Applicant.objects.filter(user=user, job_id=id).exists():
        messages.error(request, 'You already applied for this job!')
        return redirect(reverse("jobapp:single-job", kwargs={'id': id}))

    if request.method == 'POST':
        form = JobApplyForm(request.POST, request.FILES)

        if form.is_valid():
            # Check if the video file is provided
            if not request.FILES.get('video'):
                messages.error(request, 'Video introduction is required!')
                return render(request, 'jobapp/apply_job.html', {'form': form, 'job': job})

            # Save the applicant details without video first
            instance = form.save(commit=False)
            instance.user = user
            instance.job = job
            instance.save()

            try:
                # Save the video and transcribe it
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe(instance.video.path)
                transcription = result.get('text', '')

                # Calculate similarity score between job description and transcription
                similarity_score = calculate_similarity_score(job.description, transcription)
                instance.transcription = transcription
                instance.similarity_score = similarity_score

                # Save transcription and similarity score
                instance.save()

                messages.success(request, 'You have successfully applied for this job!')
                return redirect(reverse("jobapp:single-job", kwargs={'id': id}))

            except Exception as e:
                # Clean up if something went wrong
                if instance.pk:
                    instance.delete()
                messages.error(request, f'Error during transcription or scoring: {str(e)}')
                return render(request, 'jobapp/apply_job.html', {'form': form, 'job': job})
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = JobApplyForm(initial={'job': job.id})

    return render(request, 'jobapp/apply_job.html', {'form': form, 'job': job})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import Applicant
from .utils import calculate_similarity_score

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def all_applicants_view(request, id):
    """
    View for employer to see all applicants and their similarity scores.
    """
    # Fetch all applicants for the given job id and order by similarity score (descending)
    all_applicants = Applicant.objects.filter(job=id)

    # Calculate similarity score for each applicant (if it's not already calculated)
    for applicant in all_applicants:
        if applicant.transcription:  # Ensure there's a transcription to compare with
            score = calculate_similarity_score(applicant.job.description, applicant.transcription)
            applicant.similarity_score = score
            applicant.save()

    # Order applicants by similarity score in descending order
    all_applicants = all_applicants.order_by('-similarity_score')

    context = {
        'all_applicants': all_applicants
    }

    return render(request, 'jobapp/all-applicants.html', context)


@login_required(login_url=reverse_lazy('account:login'))
def dashboard_view(request):
    """
    """
    jobs = []
    savedjobs = []
    appliedjobs = []
    total_applicants = {}
    if request.user.role == 'employer':

        jobs = Job.objects.filter(user=request.user.id)
        for job in jobs:
            count = Applicant.objects.filter(job=job.id).count()
            total_applicants[job.id] = count

    if request.user.role == 'employee':
        savedjobs = BookmarkJob.objects.filter(user=request.user.id)
        appliedjobs = Applicant.objects.filter(user=request.user.id)
    context = {

        'jobs': jobs,
        'savedjobs': savedjobs,
        'appliedjobs':appliedjobs,
        'total_applicants': total_applicants
    }

    return render(request, 'jobapp/dashboard.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def delete_job_view(request, id):

    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Your Job Post was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def make_complete_job_view(request, id):
    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:
        try:
            job.is_closed = True
            job.save()
            messages.success(request, 'Your Job was marked closed!')
        except:
            messages.success(request, 'Something went wrong !')
            
    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def delete_bookmark_view(request, id):

    job = get_object_or_404(BookmarkJob, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Saved Job was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def applicant_details_view(request, id):
    applicant = get_object_or_404(User, id=id)
    
    # Get application video and details
    # First we'll get the job id from the URL parameter
    job_id = request.GET.get('job_id')
    
    # If job_id is provided, get the specific application
    if job_id:
        application = Applicant.objects.filter(
            user=applicant,
            job_id=job_id
        ).first()
    else:
        # Otherwise get the most recent application
        application = Applicant.objects.filter(
            user=applicant
        ).order_by('-timestamp').first()
        
    # Get all jobs this applicant has applied to
    applied_jobs = Applicant.objects.filter(user=applicant)
    
    context = {
        'applicant': applicant,
        'application': application,
        'applied_jobs': applied_jobs,
    }

    return render(request, 'jobapp/applicant-details.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def job_bookmark_view(request, id):

    form = JobBookmarkForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    applicant = BookmarkJob.objects.filter(user=request.user.id, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()

                messages.success(
                    request, 'You have successfully save this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:
        messages.error(request, 'You already saved this Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def job_edit_view(request, id=id):
    """
    Handle Job Update
    """
    job = get_object_or_404(Job, id=id, user=request.user.id)
    form = JobEditForm(request.POST or None, instance=job)
    categories = Category.objects.all()
    
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        # for save tags
        # form.save_m2m()
        messages.success(request, 'Your Job Post Was Successfully Updated!')
        return redirect(reverse("jobapp:single-job", kwargs={
            'id': instance.id
        }))
    
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/job-edit.html', context)

def about_us(request):
    return render(request, "jobapp/about_us.html", {})

def contact(request):
    form = ContactForm(request.POST or None)
    if form.is_valid():
        instance = form.save()
        instance.save()
        return redirect('/')
    context = {
        'form': form
    }
    if request.method == "POST":
        email= request.POST.get('email')
        name= request.POST.get('name')
        message = request.POST.get('message')
        print(email,name,message)
        send_mail(
           "Job Portal - Chat",
           name + "-" + message,
           email,
           ["*"],
           fail_silently=False,
        )
    return render(request, "jobapp/contact.html", context)