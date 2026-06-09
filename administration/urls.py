from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    # Панели
    path('moderator/', views.moderator_panel, name='moderator_panel'),
    path('admin/', views.admin_panel, name='admin_panel'),
    
    # Управление пользователями (ТОЛЬКО АДМИН)
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/toggle-moderator/', views.toggle_moderator, name='toggle_moderator'),
    path('admin/users/<int:user_id>/toggle-admin/', views.toggle_admin, name='toggle_admin'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Управление тестами (МОДЕРАТОРЫ И АДМИНЫ)
    path('tests/', views.moderator_tests, name='moderator_tests'),
    path('results/', views.moderator_results, name='moderator_results'),
    path('result/<int:result_id>/', views.moderator_result, name='moderator_result'),
    path('create-test/', views.moderator_create_test, name='moderator_create_test'),
    path('category/add/', views.add_category, name='add_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('test/<int:test_id>/questions/', views.moderator_questions, name='moderator_questions'),
    path('test/<int:test_id>/edit/', views.moderator_edit_test, name='moderator_edit_test'),
    path('test/<int:test_id>/delete/', views.moderator_delete_test, name='moderator_delete_test'),
    path('test/<int:test_id>/subscribers/', views.moderator_subscribers, name='moderator_subscribers'),
    path('test/<int:test_id>/assign/', views.assign_subscriber, name='assign_subscriber'),
    path('test/<int:test_id>/subscription/<int:sub_id>/delete/', views.delete_subscription, name='delete_subscription'),
    path('question/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('test/<int:test_id>/add-question/', views.moderator_add_question, name='moderator_add_question'),
    path('result/<int:result_id>/delete/', views.delete_result, name='delete_result'),
]