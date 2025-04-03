from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from .utils import parse_cv

def upload_cv(request):
    if request.method == 'POST' and request.FILES.get('cv_file'):
        try:
            # Handle file upload
            cv_file = request.FILES['cv_file']
            fs = FileSystemStorage()
            
            # Save the uploaded file
            filename = fs.save(f'cv_uploads/{cv_file.name}', cv_file)
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            
            # Parse the CV
            parsed_data = parse_cv(file_path)
            
            # Delete the uploaded file after processing
            fs.delete(filename)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'data': parsed_data})
            
            return render(request, 'cv_parser/results.html', {
                'parsed_data': parsed_data
            })
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': str(e)})
            return render(request, 'cv_parser/upload.html', {
                'error': str(e)
            })
    
    return render(request, 'cv_parser/upload.html')