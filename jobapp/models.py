from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager

User = get_user_model()

class Contact(models.Model):
    Email = models.EmailField()
    name = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.name

JOB_TYPE = (
    ('1', "Full time"),
    ('2', "Part time"),
    ('3', "Internship"),
)

class Category(models.Model):
    name = models.CharField(max_length=255, default="Uncategorized")  # Added default
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name  # Return name directly

class Job(models.Model):
    user = models.ForeignKey(User, related_name='User', on_delete=models.CASCADE) 
    title = models.CharField(max_length=300)
    description = RichTextField()
    tags = TaggableManager()
    location = models.CharField(max_length=300)
    job_type = models.CharField(choices=JOB_TYPE, max_length=1)
    category = models.ForeignKey(Category, related_name='jobs', on_delete=models.CASCADE, null=True, blank=True)
    salary = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=300)
    company_description = RichTextField(blank=True, null=True)
    url = models.URLField(max_length=200)
    last_date = models.DateField()
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)
    Vacancy = models.CharField(max_length=10, null=True)
    Experience = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=30)
    passedout = models.CharField(max_length=30)

    def __str__(self):
        return self.title

class Applicant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    video = models.FileField(upload_to='applicant_videos/', null=True, blank=True)
    transcription = models.TextField(null=True, blank=True)
    similarity_score = models.FloatField(null=True, blank=True)  # To store similarity score

    def __str__(self):
        return self.job.title

class BookmarkJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.job.title

class Video(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos', null=True, default=1)
    file = models.FileField(upload_to='videos/')

    def __str__(self):
        return f"{self.user.username}'s video"