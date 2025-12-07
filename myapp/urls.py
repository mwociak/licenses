from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    path('api/verify', views.verify_license_api, name='verify_license_api'),
    path('api/generate_trial', views.register_and_generate_trial_api, name='register_and_generate_trial_api'),
    # Ten endpoint jest bardziej do testowania
    path('api/get_machine_id', views.get_machine_id_api, name='get_machine_id_api'),
]
