from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg, Count
from tests.models import Test, TestCategory, Question, Answer, TestResult, TestSubscription, UserAnswer
from accounts.models import User
from .forms import TestForm, CategoryForm, QuestionForm
from utils.timezone_utils import format_novosibirsk, parse_datetime_novosibirsk
import os
import json


# ========== ДЕКОРАТОРЫ ==========

def moderator_required(view_func):
   
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_moderator or request.user.is_admin):
            messages.error(request, 'Доступ запрещен')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin:
            messages.error(request, 'Доступ запрещен')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


# ========== ПАНЕЛИ ==========

@moderator_required
def moderator_panel(request):
  
    my_tests = Test.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'my_tests': my_tests,
        'current_user': request.user,
    }
    return render(request, 'administration/moderator/moderator_panel.html', context)


@admin_required
def admin_panel(request):
   
    total_users = User.objects.count()
    total_tests = Test.objects.count()
    total_results = TestResult.objects.filter(completed_at__isnull=False).count()

    my_tests = Test.objects.filter(created_by=request.user).order_by('-id')[:5]
    
    recent_results = TestResult.objects.filter(
        completed_at__isnull=False
    ).order_by('-completed_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_tests': total_tests,
        'total_results': total_results,
        'recent_results': recent_results,
        'my_tests': my_tests,
        
    }
    return render(request, 'administration/admin/admin_panel.html', context)


# ========== УПРАВЛЕНИЕ ТЕСТАМИ (МОДЕРАТОРЫ) ==========

@moderator_required
def moderator_tests(request):
    """Все тесты в системе с поиском и фильтрацией"""
    all_tests = Test.objects.all().order_by('-created_at')
    
    # Получаем все категории для фильтра
    categories = TestCategory.objects.all().order_by('name')
    
    # ПОИСК по названию
    search_query = request.GET.get('search', '')
    if search_query:
        all_tests = all_tests.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # ПОИСК по автору
    author_query = request.GET.get('author', '')
    if author_query:
        all_tests = all_tests.filter(
            Q(created_by__first_name__icontains=author_query) |
            Q(created_by__last_name__icontains=author_query) |
            Q(created_by__username__icontains=author_query)
        )
    
    # ФИЛЬТР по категории
    category_id = request.GET.get('category')
    if category_id:
        all_tests = all_tests.filter(category_id=category_id)
    
    # ФИЛЬТР по сложности
    difficulty = request.GET.get('difficulty')
    if difficulty:
        all_tests = all_tests.filter(difficulty=difficulty)
    
    # ФИЛЬТР по типу доступа
    access_type = request.GET.get('access_type')
    if access_type == 'public':
        all_tests = all_tests.filter(access_type='public')
    elif access_type == 'subscribed':
        all_tests = all_tests.filter(access_type='subscribed')
    
    # ФИЛЬТР по дате создания
    date_from = request.GET.get('date_from')
    if date_from:
        all_tests = all_tests.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        all_tests = all_tests.filter(created_at__date__lte=date_to)
    

    context = {
        'all_tests': all_tests,
        'categories': categories,
        'search_query': search_query,
        'author_query': author_query,
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'selected_access': access_type,
        'date_from': date_from,
        'date_to': date_to,
        'current_user': request.user,
    }
    return render(request, 'administration/moderator/moderator_all_tests.html', context)


@moderator_required
def moderator_create_test(request):
   
    categories = TestCategory.objects.all().order_by('name')
    
    if request.method == 'POST':
        print("POST данные получены:")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        
        form = TestForm(request.POST)
        if form.is_valid():
            print("Форма валидна!")
            test = form.save(commit=False)
            test.created_by = request.user
            test.time_limit = form.cleaned_data['time_limit'] * 60
            test.save()
            print(f"Тест создан с ID: {test.id}")
            messages.success(request, 'Тест успешно создан! Теперь добавьте вопросы.')
            return redirect('administration:moderator_questions', test_id=test.id)
        else:
            print("Форма не валидна. Ошибки:")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"{field}: {error}")
                    messages.error(request, f'{field}: {error}')
    else:
        print("GET запрос - показываем форму")
        form = TestForm()
    
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'administration/moderator/create_test.html', context)


@moderator_required
def moderator_questions(request, test_id):

    test = get_object_or_404(Test, id=test_id) 
    
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'Доступ запрещен')
        return redirect('administration:moderator_panel')
    
    questions = Question.objects.filter(test=test).prefetch_related('answers')
    
    context = {
        'test': test, 
        'questions': questions,
    }
    return render(request, 'administration/moderator/add_questions.html', context)


@moderator_required
def moderator_add_question(request, test_id):
   
    if request.method != 'POST':
        return redirect('administration:moderator_questions', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id)
    
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'Доступ запрещен')
        return redirect('administration:moderator_panel')
    
  
    question_text = request.POST.get('question_text', '').strip()
    question_type = request.POST.get('question_type', 'single')
    topic = request.POST.get('topic', '').strip()
    question_level = request.POST.get('question_level', 'medium')
    
    try:
        points = int(request.POST.get('points', 1))
    except ValueError:
        points = 1
    
    if not question_text:
        messages.error(request, 'Введите текст вопроса')
        return redirect('administration:moderator_questions', test_id=test_id)
    
    # Создаем вопрос
    question = Question.objects.create(
        test=test,
        text=question_text,
        question_type=question_type,
        points=points,
        topic=topic,
        question_level=question_level,
        last_modified_by=request.user
    )
    
  
    if 'image' in request.FILES:
        question.image = request.FILES['image']
        question.save()
    
  
    if question_type in ['single', 'multiple']:
        i = 0
        answers_added = False
        while True:
            answer_text = request.POST.get(f'question-answers-{i}-text')
            if not answer_text:
                i += 1
                if i > 20: 
                    break
                continue
            
            if question_type == 'single':
                correct_answer_index = request.POST.get('correct_answer')
                is_correct = (correct_answer_index == str(i))
            else:  
                is_correct = request.POST.get(f'question-answers-{i}-is_correct') == 'true'
            
          
            Answer.objects.create(
                question=question,
                text=answer_text.strip(),
                is_correct=is_correct
            )
            answers_added = True
            i += 1
        
        if not answers_added:
            messages.warning(request, 'Вопрос создан без вариантов ответа')
    
    elif question_type == 'text':
        text_answer = request.POST.get('text_correct_answer', '').strip()
        if text_answer:
            Answer.objects.create(
                question=question,
                text=text_answer.lower(),
                is_correct=True
            )
        else:
            messages.warning(request, 'Текстовый вопрос создан без правильного ответа')
    
    messages.success(request, 'Вопрос успешно добавлен!')
    return redirect('administration:moderator_questions', test_id=test_id)


@moderator_required
def question_edit(request, question_id):
    """Редактирование вопроса"""
    question = get_object_or_404(Question, id=question_id)
    test = question.test
    
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'Доступ запрещен')
        return redirect('administration:moderator_panel')
    
    if request.method == 'POST':
        question.text = request.POST.get('question_text', '').strip()
        question.question_type = request.POST.get('question_type', 'single')
        question.points = int(request.POST.get('points', 1))
        question.topic = request.POST.get('topic', '').strip()
        question.question_level = request.POST.get('question_level', 'medium')
        question.save()
        
        # Обновляем ответы
        if question.question_type != 'text':
            question.answers.all().delete()
            
            i = 0
            while True:
                answer_text = request.POST.get(f'answers_{i}_text')
                if not answer_text:
                    i += 1
                    if i > 20:
                        break
                    continue
                
                if question.question_type == 'single':
                    correct_answer_index = request.POST.get('correct_answer')
                    is_correct = (correct_answer_index == str(i))
                else:
                    is_correct = request.POST.get(f'answers_{i}_correct') == '1'
                
                Answer.objects.create(
                    question=question,
                    text=answer_text.strip(),
                    is_correct=is_correct
                )
                i += 1
        
        messages.success(request, 'Вопрос обновлен')
        return redirect('administration:moderator_questions', test_id=test.id)
    
    context = {
        'question': question,
    }
    return render(request, 'administration/moderator/add_questions.html')


@moderator_required
def question_delete(request, question_id):
   
    if request.method != 'POST':
        return redirect('administration:moderator_panel')
    
    question = get_object_or_404(Question, id=question_id)
    test_id = question.test.id
    
    if question.test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'У вас нет прав на удаление этого вопроса')
        return redirect('administration:moderator_questions', test_id=test_id)
    
    question.delete()
    messages.success(request, 'Вопрос успешно удален')
    return redirect('administration:moderator_questions', test_id=test_id)


@moderator_required
def moderator_delete_test(request, test_id):
    """Удаление теста"""
    if request.method != 'POST':
        return redirect('administration:moderator_panel')
    
    test = get_object_or_404(Test, id=test_id)
    
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'Вы не можете удалить этот тест')
        return redirect('administration:moderator_panel')
    
    test_title = test.title
    
    # Каскадное удаление через Django ORM
    test.delete()
    
    messages.success(request, f'Тест "{test_title}" успешно удален')
    return redirect('administration:moderator_panel')

@moderator_required
def moderator_edit_test(request, test_id):
 
    test = get_object_or_404(Test, id=test_id)
    
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'У вас нет прав на редактирование этого теста')
        return redirect('administration:moderator_panel')
    
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тест обновлен')
            return redirect('administration:moderator_panel')
    else:
        form = TestForm(instance=test)
    
    categories = TestCategory.objects.all()
    context = {
        'form': form,
        'test': test,
        'categories': categories,
    }
    return render(request, 'administration/moderator/create_test.html', context)

# ========== УПРАВЛЕНИЕ КАТЕГОРИЯМИ ==========

@moderator_required
def add_category(request):
    """Добавление новой категории"""
    if request.method == 'POST':
        name = request.POST.get('category_name', '').strip()
        description = request.POST.get('category_description', '').strip()
        
        if not name:
            messages.warning(request, 'Введите название категории.')
            return redirect(request.META.get('HTTP_REFERER', 'administration:moderator_create_test'))
        
        # Создаем категорию (created_at заполнится автоматически)
        category = TestCategory.objects.create(
            name=name,
            description=description
        )
        messages.success(request, f'Категория "{name}" создана.')
    
    return redirect(request.META.get('HTTP_REFERER', 'administration:moderator_create_test'))


@moderator_required
def delete_category(request, category_id):
    """Удаление категории"""
    if request.method != 'POST':
        return redirect('administration:moderator_create_test')
    
    category = get_object_or_404(TestCategory, id=category_id)
    category_name = category.name
    
    # Переводим тесты в состояние "Без категории"
    Test.objects.filter(category=category).update(category=None)
    category.delete()
    
    messages.info(request, f'Категория "{category_name}" удалена. Тесты переведены в "Без категории".')
    
    # ВАЖНО: Перенаправляем обратно на страницу создания теста
    return redirect('administration:moderator_create_test')  # ИСПРАВЛЕНО: убран context


# ========== ПОДПИСЧИКИ ТЕСТОВ ==========

@moderator_required
def moderator_subscribers(request, test_id):
    """Список подписанных пользователей для теста по подписке"""
    test = get_object_or_404(Test, id=test_id)
    
    if test.access_type != 'subscribed':
        messages.info(request, 'Этот тест не является тестом по подписке.')
        return redirect('administration:moderator_panel')
    
    subscriptions = TestSubscription.objects.filter(test=test).select_related('worker')
    workers = User.objects.order_by('last_name', 'first_name').all()
    
    now_nsk = timezone.localtime(timezone.now())
    
    subscriptions_display = [
        {
            'sub': s,
            'subscribed_at_display': format_novosibirsk(s.subscribed_at) or '—',
            'valid_from_display': format_novosibirsk(s.valid_from) or '—',
            'valid_until_display': format_novosibirsk(s.valid_until) or 'Без ограничения'
        }
        for s in subscriptions
    ]
    
    context = {
        'test': test,
        'subscriptions_display': subscriptions_display,
        'workers': workers,
        'now_nsk': now_nsk,
    }
    return render(request, 'administration/moderator/moderator_subscribers.html', context)


def parse_datetime_novosibirsk(date_str, time_str):
    """Парсит дату/время (ДД.ММ.ГГГГ, ЧЧ:ММ) как время в Новосибирске, возвращает UTC"""
    if not date_str or not time_str:
        return None
    try:
        parts = date_str.strip().split('.')
        tparts = time_str.strip().split(':')
        if len(parts) == 3 and len(tparts) >= 2:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            h, m = int(tparts[0]), int(tparts[1])
            return novosibirsk_to_utc(day, month, year, h, m)
    except (ValueError, IndexError):
        pass
    return None


@moderator_required
def assign_subscriber(request, test_id):
    """Назначить тест конкретному пользователю"""
    if request.method != 'POST':
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id)
    
    if test.access_type != 'subscribed':
        messages.info(request, 'Назначение доступно только для тестов по подписке.')
        return redirect('administration:moderator_panel')
    
    worker = None
    worker_id = request.POST.get('worker_id')
    email_manual = request.POST.get('email_manual', '').strip()
    
    if email_manual:
        try:
            worker = User.objects.get(email=email_manual)
        except User.DoesNotExist:
            messages.error(request, f'Пользователь с email "{email_manual}" не найден.')
            return redirect('administration:moderator_subscribers', test_id=test_id)
    elif worker_id:
        try:
            worker = User.objects.get(id=worker_id)
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден.')
            return redirect('administration:moderator_subscribers', test_id=test_id)
    else:
        messages.warning(request, 'Выберите пользователя из списка или введите email.')
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    # Проверяем, не назначен ли уже тест
    existing = TestSubscription.objects.filter(worker=worker, test=test).first()
    if existing:
        messages.info(request, 'Этот тест уже назначен выбранному пользователю.')
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    # Парсим даты
    valid_from = parse_datetime_novosibirsk(
        request.POST.get('valid_from_date'),
        request.POST.get('valid_from_time')
    )
    valid_until = parse_datetime_novosibirsk(
        request.POST.get('valid_until_date'),
        request.POST.get('valid_until_time')
    )
    
    if not valid_from:
        valid_from = timezone.now()
    
    # Создаем подписку
    subscription = TestSubscription.objects.create(
        worker=worker,
        test=test,
        valid_from=valid_from,
        valid_until=valid_until
    )
    
    messages.success(request, f'Тест "{test.title}" назначен пользователю {worker.get_full_name()}.')
    return redirect('administration:moderator_subscribers', test_id=test_id)


@moderator_required
def delete_subscription(request, test_id, sub_id):
    """Снять назначение теста с пользователя"""
    if request.method != 'POST':
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    subscription = get_object_or_404(TestSubscription, id=sub_id, test_id=test_id)
    subscription.delete()
    
    messages.info(request, 'Назначение теста для пользователя удалено.')
    return render(request, 'administration/moderator/moderator_subscribers.html', context)


# ========== РЕЗУЛЬТАТЫ ТЕСТОВ ==========

@moderator_required
def moderator_results(request):
    """Просмотр всех результатов тестов с поиском и фильтрацией"""
    results = TestResult.objects.filter(
        completed_at__isnull=False
    ).select_related('worker', 'test').order_by('-completed_at')
    
    # ПОИСК по пользователю
    user_query = request.GET.get('user', '')
    if user_query:
        results = results.filter(
            Q(worker__first_name__icontains=user_query) |
            Q(worker__last_name__icontains=user_query) |
            Q(worker__email__icontains=user_query) |
            Q(worker__username__icontains=user_query)
        )
    
    # ПОИСК по тесту
    test_query = request.GET.get('test', '')
    if test_query:
        results = results.filter(
            Q(test__title__icontains=test_query) |
            Q(test__description__icontains=test_query)
        )
    
    # ФИЛЬТР по статусу
    status = request.GET.get('status', '')
    if status == 'passed':
        results = results.filter(passed=True)
    elif status == 'failed':
        results = results.filter(passed=False)
    elif status == 'in_progress':
        results = results.filter(completed_at__isnull=True)
    
    # ФИЛЬТР по дате завершения
    date_from = request.GET.get('date_from')
    if date_from:
        results = results.filter(completed_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        results = results.filter(completed_at__date__lte=date_to)
    
    # ФИЛЬТР по проценту
    min_percent = request.GET.get('min_percent')
    if min_percent:
        try:
            results = results.filter(percentage__gte=float(min_percent))
        except ValueError:
            pass
    
    max_percent = request.GET.get('max_percent')
    if max_percent:
        try:
            results = results.filter(percentage__lte=float(max_percent))
        except ValueError:
            pass
    
    # Статистика
    total_results = TestResult.objects.filter(completed_at__isnull=False).count()
    passed_count = TestResult.objects.filter(completed_at__isnull=False, passed=True).count()
    failed_count = TestResult.objects.filter(completed_at__isnull=False, passed=False).count()
    
    avg_percentage = TestResult.objects.filter(
        completed_at__isnull=False
    ).aggregate(Avg('percentage'))['percentage__avg'] or 0
    
    # Экспорт в CSV
    if request.GET.get('export') == 'csv':
        return export_results_csv(results)
    
    context = {
        'results': results,
        'user_query': user_query,
        'test_query': test_query,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'min_percent': min_percent,
        'max_percent': max_percent,
        'total_results': total_results,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'avg_percentage': avg_percentage,
    }
    return render(request, 'administration/moderator/moderator_results.html', context)

    


@moderator_required
def delete_result(request, result_id):
    """Удаление результата теста"""
    if request.method != 'POST':
        return redirect('administration:moderator_results')
    
    result = get_object_or_404(TestResult, id=result_id)
    
    # Сохраняем информацию для сообщения
    user_name = result.worker.get_full_name() if result.worker else 'Пользователь'
    test_title = result.test.title if result.test else 'тест'
    
    # Удаляем связанные ответы
    UserAnswer.objects.filter(result=result).delete()
    
    # Удаляем результат
    result.delete()
    
    messages.success(request, f'Результат теста "{test_title}" для {user_name} удален')
    return redirect('administration:moderator_results')


@moderator_required
def moderator_result(request, result_id):
    """Детальный просмотр результата теста"""
    result = get_object_or_404(TestResult, id=result_id)
    
    user_answers = UserAnswer.objects.filter(result=result).select_related('question')
    
    detailed_answers = []
    for ua in user_answers:
        question = ua.question
        answer_ids = []
        answers = []
        
        if hasattr(ua, 'selected_answers'):
            answers = ua.selected_answers.all()
            answer_ids = [a.id for a in answers]
        
        correct_answers = question.answers.filter(is_correct=True)
        
        detailed_answers.append({
            'question': question,
            'user_answers': answers,
            'correct_answers': correct_answers,
            'is_correct': ua.is_correct,
            'ua': ua,
        })
    
    context = {
        'result': result,
        'detailed_answers': detailed_answers,
    }
    return render(request, 'administration/moderator/moderator_result.html', context)


# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (АДМИН) ==========

@admin_required
def admin_users(request):
    """Список всех пользователей с поиском и фильтрацией"""
    users = User.objects.all().order_by('-created_at')
    
    # Получаем уникальные специализации для фильтра
    specializations = User.objects.exclude(
        specialization__isnull=True
    ).exclude(
        specialization=''
    ).values_list('specialization', flat=True).distinct().order_by('specialization')
    
    # ПОИСК по имени, фамилии, email или должности
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    # ФИЛЬТР по специализации
    specialization = request.GET.get('specialization', '')
    if specialization:
        users = users.filter(specialization=specialization)
    
    # ФИЛЬТР по роли
    role = request.GET.get('role', '')
    if role == 'admin':
        users = users.filter(is_admin=True)
    elif role == 'moderator':
        users = users.filter(is_moderator=True, is_admin=False)
    elif role == 'user':
        users = users.filter(is_admin=False, is_moderator=False)
    
    context = {
        'users': users,
        'specializations': specializations,
        'current_user': request.user,
        'search_query': search_query,
        'selected_specialization': specialization,
        'selected_role': role,
    }
    return render(request, 'administration/admin/admin_users.html', context)


@admin_required
def toggle_admin(request, user_id):
    """Назначить/снять администратора"""
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.warning(request, 'Нельзя изменить свои собственные права администратора')
        return redirect('administration:admin_users')
    
    user.is_admin = not user.is_admin
    user.save()
    
    status = 'назначен' if user.is_admin else 'снят'
    messages.success(request, f'Пользователь {user.get_full_name()} {status} администратором')
    return render(request, 'administration/admin/admin_users.html')



@admin_required
def toggle_admin(request, user_id):
    """Назначить/снять администратора"""
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.warning(request, 'Нельзя изменить свою собственную роль')
        return redirect('administration:admin_users')
    
    user.is_admin = not user.is_admin
    user.save()
    
    status = 'назначен' if user.is_admin else 'снят'
    messages.success(request, f'Пользователь {user.get_full_name()} {status} администратором')
    return redirect('administration:admin_users')


@moderator_required
def delete_subscription(request, test_id, sub_id):
    """Снять назначение теста с пользователя"""
    if request.method != 'POST':
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    try:
        subscription = TestSubscription.objects.get(id=sub_id, test_id=test_id)
        subscription.delete()
        messages.info(request, 'Назначение теста для пользователя удалено.')
    except TestSubscription.DoesNotExist:
        messages.error(request, 'Подписка не найдена или уже была удалена.')
    
    return redirect('administration:moderator_subscribers', test_id=test_id)

# ========== УПРАВЛЕНИЕ ПОДПИСКАМИ ==========

@moderator_required
def moderator_subscribers(request, test_id):
    """Список подписанных пользователей для теста по подписке"""
    test = get_object_or_404(Test, id=test_id)
    
    if test.access_type != 'subscribed':
        messages.info(request, 'Этот тест не является тестом по подписке.')
        return redirect('administration:moderator_panel')
    
    subscriptions = TestSubscription.objects.filter(test=test).select_related('worker')
    workers = User.objects.order_by('last_name', 'first_name').all()
    
    now_nsk = timezone.localtime(timezone.now())
    
    subscriptions_display = [
        {
            'sub': s,
            'subscribed_at_display': format_novosibirsk(s.subscribed_at) or '—',
            'valid_from_display': format_novosibirsk(s.valid_from) or '—',
            'valid_until_display': format_novosibirsk(s.valid_until) or 'Без ограничения'
        }
        for s in subscriptions
    ]
    
    context = {
        'test': test,
        'subscriptions_display': subscriptions_display,
        'workers': workers,
        'now_nsk': now_nsk,
    }
    return render(request, 'administration/moderator/moderator_subscribers.html', context)


def parse_datetime_novosibirsk(date_str, time_str):
    """Парсит дату/время (ДД.ММ.ГГГГ, ЧЧ:ММ) как время в Новосибирске, возвращает UTC"""
    if not date_str or not time_str:
        return None
    try:
        parts = date_str.strip().split('.')
        tparts = time_str.strip().split(':')
        if len(parts) == 3 and len(tparts) >= 2:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            h, m = int(tparts[0]), int(tparts[1])
            return novosibirsk_to_utc(day, month, year, h, m)
    except (ValueError, IndexError):
        pass
    return None


@moderator_required
def assign_subscriber(request, test_id):
    """Назначить тест конкретному пользователю"""
    if request.method != 'POST':
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id)
    
    if test.access_type != 'subscribed':
        messages.info(request, 'Назначение доступно только для тестов по подписке.')
        return redirect('administration:moderator_panel')
    
    worker = None
    worker_id = request.POST.get('worker_id')
    email_manual = request.POST.get('email_manual', '').strip()
    
    if email_manual:
        try:
            worker = User.objects.get(email=email_manual)
        except User.DoesNotExist:
            messages.error(request, f'Пользователь с email "{email_manual}" не найден.')
            return redirect('administration:moderator_subscribers', test_id=test_id)
    elif worker_id:
        try:
            worker = User.objects.get(id=worker_id)
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден.')
            return redirect('administration:moderator_subscribers', test_id=test_id)
    else:
        messages.warning(request, 'Выберите пользователя из списка или введите email.')
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    # Проверяем, не назначен ли уже тест
    existing = TestSubscription.objects.filter(worker=worker, test=test).first()
    if existing:
        messages.info(request, 'Этот тест уже назначен выбранному пользователю.')
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    # Парсим даты
    from utils.timezone_utils import parse_datetime_novosibirsk
    
    valid_from = parse_datetime_novosibirsk(
        request.POST.get('valid_from_date'),
        request.POST.get('valid_from_time')
    )
    valid_until = parse_datetime_novosibirsk(
        request.POST.get('valid_until_date'),
        request.POST.get('valid_until_time')
    )
    
    if not valid_from:
        valid_from = timezone.now()
    
    # Создаем подписку
    subscription = TestSubscription.objects.create(
        worker=worker,
        test=test,
        valid_from=valid_from,
        valid_until=valid_until
    )
    
    messages.success(request, f'Тест "{test.title}" назначен пользователю {worker.get_full_name()}.')
    return redirect('administration:moderator_subscribers', test_id=test_id)


@moderator_required
def delete_subscription(request, test_id, sub_id):
    """Снять назначение теста с пользователя"""
    if request.method != 'POST':
        return redirect('administration:moderator_subscribers', test_id=test_id)
    
    try:
        subscription = TestSubscription.objects.get(id=sub_id, test_id=test_id)
        subscription.delete()
        messages.info(request, 'Назначение теста для пользователя удалено.')
    except TestSubscription.DoesNotExist:
        messages.error(request, 'Подписка не найдена или уже была удалена.')
    
    return redirect('administration:moderator_subscribers', test_id=test_id)
@moderator_required
def moderator_edit_test(request, test_id):
    """Редактирование теста"""
    test = get_object_or_404(Test, id=test_id)
    
    # Проверка прав
    if test.created_by != request.user and not request.user.is_admin:
        messages.error(request, 'У вас нет прав на редактирование этого теста')
        return redirect('administration:moderator_panel')
    
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тест обновлен')
            return redirect('administration:moderator_panel')
    else:
        form = TestForm(instance=test)
    
    categories = TestCategory.objects.all()
    context = {
        'form': form,
        'test': test,
        'categories': categories,
    }
    return render(request, 'administration/create_test.html', context)


@moderator_required
def moderator_add_category(request):
    """Добавление новой категории"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            category = TestCategory.objects.create(
                name=name,
                description=description
            )
            messages.success(request, f'Категория "{name}" создана!')
        else:
            messages.error(request, 'Название категории обязательно')
    
    return redirect('administration:moderator_create_test')


@moderator_required
def moderator_delete_category(request, category_id):
    """Удаление категории"""
    if request.method == 'POST':
        category = get_object_or_404(TestCategory, id=category_id)
        category_name = category.name
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена')
    
    return redirect('administration:moderator_create_test')

@admin_required
def delete_user(request, user_id):
    """Удалить пользователя"""
    if request.method != 'POST':
        return redirect('administration:admin_users')
    
    user = get_object_or_404(User, id=user_id)
    
    # Нельзя удалить самого себя
    if user.id == request.user.id:
        messages.error(request, 'Нельзя удалить свой собственный аккаунт')
        return redirect('administration:admin_users')
    
    # Удаляем связанные данные
    TestResult.objects.filter(worker=user).delete()
    TestSubscription.objects.filter(worker=user).delete()
    
    username = user.get_full_name()
    user.delete()
    
    messages.success(request, f'Пользователь {username} удален')
    return redirect('administration:admin_users')

@admin_required
def toggle_moderator(request, user_id):
    """Назначить/снять модератора"""
    user = get_object_or_404(User, id=user_id)
    
    # Нельзя менять свою роль
    if user.id == request.user.id:
        messages.warning(request, 'Нельзя изменить свою собственную роль')
        return redirect('administration:admin_users')
    
    user.is_moderator = not user.is_moderator
    user.save()
    
    status = 'назначен' if user.is_moderator else 'снят'
    messages.success(request, f'Пользователь {user.get_full_name()} {status} модератором')
    return redirect('administration:admin_users')