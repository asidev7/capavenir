from django.urls import path

from . import views

app_name = "orientation"

urlpatterns = [
    path("orientation/", views.start, name="start"),
    path("orientation/<int:session_id>/", views.chat, name="chat"),
    path("orientation/<int:session_id>/save/", views.save_answers, name="save_answers"),
    path("orientation/<int:session_id>/upload-notes/", views.upload_transcript, name="upload_transcript"),
    path("orientation/<int:session_id>/generer/", views.generate, name="generate"),
    path("orientation/<int:session_id>/status/", views.status, name="status"),
    path("api/subjects/", views.subjects_for_serie, name="subjects_for_serie"),
    path("rapport/<int:report_id>/", views.report, name="report"),
    path("rapport/<int:report_id>/pdf/", views.report_pdf, name="report_pdf"),
]
