from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    path('', views.index, name='index'),
    path('tests/', views.test_list, name='tests'),
    path('<int:test_id>/', views.test_detail, name='detail'),
    path('<int:test_id>/start/', views.start_test, name='start'),
    path('take/<int:result_id>/', views.take_test, name='take'),
    path('result/<int:result_id>/', views.test_result, name='result'),
    path('<int:test_id>/trial/', views.trial_page, name='trial_page'),
    path('<int:test_id>/trial/start/', views.trial_start, name='trial_start'),
    path('<int:test_id>/trial/take/', views.trial_take, name='trial_take'),
    path('<int:test_id>/trial/submit/', views.trial_submit, name='trial_submit'),
]