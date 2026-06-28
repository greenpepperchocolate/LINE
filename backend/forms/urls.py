from django.urls import path

from . import views

# プレフィックス: /api/
urlpatterns = [
    path("forms", views.forms_list),
    path("forms/<uuid:form_id>", views.form_detail),
    path("forms/<uuid:form_id>/submissions", views.form_submissions),
]
