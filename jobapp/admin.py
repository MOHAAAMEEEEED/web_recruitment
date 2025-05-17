# from django.contrib import admin
# from .models import *
# from .models import Category


# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description')
#     list_filter = ('name',)
#     search_fields = ('name', 'description')

# admin.site.register(Category, CategoryAdmin)
# # admin.site.register(Category)

# class ApplicantAdmin(admin.ModelAdmin):
#     list_display = ('job','user','timestamp')
    
# admin.site.register(Applicant,ApplicantAdmin)

# class JobAdmin(admin.ModelAdmin):
#     list_display = ('title','category','job_type','timestamp')
#     list_filter = ('category', 'job_type', 'is_published', 'is_closed')
#     search_fields = ('title', 'description', 'company_name')

# admin.site.register(Job, JobAdmin)

# class BookmarkJobAdmin(admin.ModelAdmin):
#     list_display = ('job','user','timestamp')
# admin.site.register(BookmarkJob,BookmarkJobAdmin)



from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class JobAdmin(admin.ModelAdmin):
    readonly_fields = ('user', )
    list_display = ['title', 'job_type', 'category','is_published', 'is_closed', 'timestamp']
    list_filter = ['is_published', 'is_closed', 'timestamp']
    search_fields = ('title', 'company_name')
    fields = ('title', 'user', 'description', 'location', 'tags', 'job_type', 'category', 'salary', 'company_name', 'company_description', 'Vacancy', 'Experience', 'gender', 'last_date', 'url', 'is_published', 'is_closed')


class ContactAdmin(admin.ModelAdmin):
    list_display = ['Email','name']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    fields = ('name', 'description')

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'timestamp', 'display_video', 'similarity_score']
    search_fields = ['user__username', 'job__title']
    list_filter = ['timestamp']
    
    def display_video(self, obj):
        if obj.video:
            return mark_safe(f'<video width="150" height="100" controls><source src="{obj.video.url}"></video>')
        return "-"
    
    display_video.short_description = 'Video'

class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'question_id', 'created_at', 'display_video']
    search_fields = ['applicant__user__username', 'question_text']
    list_filter = ['created_at']
    
    def display_video(self, obj):
        if obj.video:
            return mark_safe(f'<video width="150" height="100" controls><source src="{obj.video.url}"></video>')
        return "-"
    
    display_video.short_description = 'Video Response'

class BookmarkJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'timestamp']
    search_fields = ['user__username', 'job__title']
    list_filter = ['timestamp']
    
class VideoAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_video', 'id']
    
    def display_video(self, obj):
        if obj.file:
            return mark_safe(f'<video width="150" height="100" controls><source src="{obj.file.url}"></video>')
        return "-"
    
    display_video.short_description = 'Video'
    
admin.site.register(Job, JobAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(BookmarkJob, BookmarkJobAdmin)
admin.site.register(Applicant, ApplicantAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(QuestionResponse, QuestionResponseAdmin)