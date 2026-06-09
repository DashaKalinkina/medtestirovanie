from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib import messages
from django.urls import reverse

from tests.models import TestResult
from .forms import LoginForm, RegistrationForm
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from .forms import ProfileEditForm

@csrf_protect
@ensure_csrf_cookie
def login_view(request):

    if request.user.is_authenticated:
        return redirect('tests:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                
                remember = form.cleaned_data.get('remember', False)
                if not remember:
                    request.session.set_expiry(0)
                
                messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
                
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                
                return redirect('tests:index')
        else:
        
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'title': 'Вход в систему'
    })

@csrf_protect
@ensure_csrf_cookie
def register_view(request):

    if request.user.is_authenticated:
        return redirect('main:index')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрация успешна! Теперь вы можете войти в систему.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'title': 'Регистрация'
    })


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('tests:index')



@login_required
def profile(request):

    results = TestResult.objects.filter(worker=request.user)
    
    completed_results = [r for r in results if r.completed_at]
    total_tests = len(completed_results)
    passed_tests = len([r for r in completed_results if r.passed])
    
    if total_tests > 0:
        avg_score = sum([r.percentage for r in completed_results]) / total_tests
    else:
        avg_score = 0
    
    recent_results = TestResult.objects.filter(
        worker=request.user
    ).order_by('-started_at')[:10]
    
    user = request.user
    
    context = {
        'user': user,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,  
        'avg_score': round(avg_score, 1),
        'recent_results': recent_results,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'title': 'Редактирование профиля'
    })

