from django.conf import settings  # type: ignore[reportMissingModuleSource]
from django.http import FileResponse, Http404, JsonResponse  # type: ignore[reportMissingModuleSource]
from django.views.decorators.http import require_GET  # type: ignore[reportMissingModuleSource]
import os

@require_GET
def get_log_content(request):
    file_path = os.path.join(settings.BASE_DIR, settings.LOG_FILE_PATH)

    if not os.path.exists(file_path):
        raise Http404("Log file not found")

    with open(file_path, 'r') as f:
        content = f.read()

    return JsonResponse({
        'filename': os.path.basename(file_path),
        'content': content
    })


@require_GET
def download_log(request):
    file_path = os.path.join(settings.BASE_DIR, settings.LOG_FILE_PATH)

    if not os.path.exists(file_path):
        raise Http404("Log file not found")

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='text/plain'
    )
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response
