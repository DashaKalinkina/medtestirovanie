from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
import json

from .models import Test, TestCategory, TestResult, Question, Answer, UserAnswer, TestSubscription
from accounts.models import User
from utils.timezone_utils import format_novosibirsk


def index(request):
   
    context = {}
    
    if request.user.is_authenticated:
        
        all_results = TestResult.objects.filter(
            worker=request.user
        ).order_by('-started_at')
        
        recent_results = all_results[:5]
        
        attempted_test_ids = TestResult.objects.filter(
            worker=request.user
        ).values_list('test_id', flat=True).distinct()
        
        available_tests = Test.objects.filter(
            is_active=True
        ).exclude(
            id__in=attempted_test_ids
        )[:3]
        
        total_available = Test.objects.filter(
            is_active=True
        ).exclude(
            id__in=attempted_test_ids
        ).count()
        
        context.update({
            'recent_results': recent_results,
            'available_tests': available_tests,
            'has_available_tests': available_tests.exists(),
            'total_available_tests': total_available,
        })
    
    return render(request, 'tests/index.html', context)

@login_required
def profile(request):
    """Профиль пользователя"""
    results = TestResult.objects.filter(worker=request.user)
    completed_results = results.filter(completed_at__isnull=False)
    
    total_tests = completed_results.count()
    passed_tests = completed_results.filter(passed=True).count()
    
    if total_tests > 0:
        avg_score = completed_results.aggregate(Avg('percentage'))['percentage__avg'] or 0
    else:
        avg_score = 0
    
    recent_results = results.order_by('-started_at')[:10]
    
    context = {
        'user': request.user,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'avg_score': round(avg_score, 1),
        'recent_results': recent_results,
    }
    return render(request, 'tests/profile.html', context)


@login_required
def test_list(request):
  
    tests = Test.objects.filter(is_active=True)
    categories = TestCategory.objects.all()
    
 
    category_id = request.GET.get('category_id')
    if category_id:
        tests = tests.filter(category_id=category_id)
    
  
    assigned_only = request.GET.get('assigned_only')
    if assigned_only:
        tests = tests.filter(access_type='subscribed')
    
    tests_data = []
    for test in tests:
      
        worker_results = TestResult.objects.filter(
            worker=request.user,
            test=test
        ).order_by('-started_at')
        
        completed_result = worker_results.filter(completed_at__isnull=False).first()

        in_progress_result = worker_results.filter(completed_at__isnull=True).first()
    
        if completed_result:
        
            if completed_result.passed:
                status = 'passed'
            else:
                status = 'failed'
            result_to_show = completed_result
        elif in_progress_result:
          
            status = 'failed'
            result_to_show = in_progress_result
        else:
          
            status = 'not_started'
            result_to_show = None
        
        tests_data.append({
            'test': test,
            'status': status,
            'result': result_to_show,
        })
    
    context = {
        'tests': tests_data,
        'categories': categories,
    }
    return render(request, 'tests/tests.html', context)


@login_required
def test_detail(request, test_id):
   
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    result_id = request.GET.get('result_id')
    
    if result_id:
       
        result = get_object_or_404(TestResult, id=result_id, worker=request.user)
        
        if result.completed_at:
            messages.info(request, 'Тест уже завершен.')
            return redirect('tests:result', result_id=result.id)
        
        questions = test.questions.all()
        
        if request.method == 'POST':
        
            score = 0
            total_points = 0
            
            for question in questions:
                total_points += question.points
                
                if question.question_type == 'single':
                    answer_id = request.POST.get(f'question_{question.id}')
                    if answer_id:
                        try:
                            answer = Answer.objects.get(id=int(answer_id))
                            is_correct = answer.is_correct
                            
                            user_answer = UserAnswer.objects.create(
                                result=result,
                                question=question,
                                is_correct=is_correct
                            )
                            if is_correct:
                                user_answer.selected_answers.add(answer)
                                score += question.points
                        except (ValueError, Answer.DoesNotExist):
                            pass
                
                elif question.question_type == 'multiple':
                    answer_ids = request.POST.getlist(f'question_{question.id}')
                    if answer_ids:
                        answer_ids = [int(id) for id in answer_ids]
                        correct_ids = list(question.answers.filter(is_correct=True).values_list('id', flat=True))
                        is_correct = (set(answer_ids) == set(correct_ids))
                        
                        user_answer = UserAnswer.objects.create(
                            result=result,
                            question=question,
                            is_correct=is_correct
                        )
                        if answer_ids:
                            user_answer.selected_answers.set(answer_ids)
                        if is_correct:
                            score += question.points
                
                elif question.question_type == 'text':
                    text_answer = request.POST.get(f'question_text_{question.id}', '').strip()
                    if text_answer:
                        correct_answer = question.answers.filter(is_correct=True).first()
                        is_correct = False
                        if correct_answer:
                            is_correct = (text_answer.lower() == correct_answer.text.lower())
                        
                        UserAnswer.objects.create(
                            result=result,
                            question=question,
                            text_answer=text_answer,
                            is_correct=is_correct
                        )
                        if is_correct:
                            score += question.points
            
            percentage = (score / total_points * 100) if total_points > 0 else 0
            passed = percentage >= test.passing_score
            
            result.score = score
            result.percentage = percentage
            result.passed = passed
            result.completed_at = timezone.now()
            result.time_taken = (result.completed_at - result.started_at).seconds
            result.save()
            
            messages.success(request, f'Тест завершен! Ваш результат: {percentage:.1f}%')
            return redirect('tests:result', result_id=result.id)
        
        # Показываем страницу с вопросами (GET запрос)
        context = {
            'test': test,
            'questions': questions,
            'result': result,
            'is_taking': True,
        }
        return render(request, 'tests/test_detail.html', context)
    
    # Режим просмотра информации о тесте (без result_id)
    # Проверяем, есть ли уже завершенный результат
    completed_result = TestResult.objects.filter(
        worker=request.user,
        test=test,
        completed_at__isnull=False
    ).first()
    
    if completed_result:
        messages.info(request, 'Вы уже прошли этот тест.')
        return redirect('tests:result', result_id=completed_result.id)
    

    if test.access_type == 'subscribed':
        subscription = TestSubscription.objects.filter(
            worker=request.user,
            test=test
        ).first()
        if not subscription:
            messages.warning(request, 'Этот тест недоступен для вашего аккаунта.')
            return redirect('tests:tests')
        
        now = timezone.now()
        if subscription.valid_from and now < subscription.valid_from:
            messages.warning(request, 'Тест будет доступен с указанной даты и времени.')
            return redirect('tests:tests')
        if subscription.valid_until and now > subscription.valid_until:
            messages.warning(request, 'Срок прохождения теста истёк.')
            return redirect('tests:tests')
    
   
    if test.max_attempts and test.max_attempts > 0:
        attempts_count = TestResult.objects.filter(
            worker=request.user,
            test=test
        ).count()
        if attempts_count >= test.max_attempts:
            messages.warning(request, f'Достигнут лимит попыток для этого теста (макс. {test.max_attempts}).')
            last_result = TestResult.objects.filter(
                worker=request.user,
                test=test,
                completed_at__isnull=False
            ).order_by('-completed_at').first()
            if last_result:
                return redirect('tests:result', result_id=last_result.id)
            return redirect('tests:tests')
    
 
    context = {
        'test': test,
        'questions': test.questions.all(),
        'is_taking': False,
    }
    return render(request, 'tests/test_detail.html', context)
@login_required
def start_test(request, test_id):
    """Начало нового теста"""
    # Убираем проверку на POST
    # if request.method != 'POST':
    #     return redirect('tests:detail', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    # Если тест по подписке — проверяем наличие подписки
    if test.access_type == 'subscribed':
        subscription = TestSubscription.objects.filter(
            worker=request.user,
            test=test
        ).first()
        if not subscription:
            messages.warning(request, 'Этот тест недоступен для вашего аккаунта.')
            return redirect('tests:detail', test_id=test_id)
        
        now = timezone.now()
        if subscription.valid_from and now < subscription.valid_from:
            messages.warning(request, 'Тест будет доступен с указанной даты и времени.')
            return redirect('tests:tests')
        if subscription.valid_until and now > subscription.valid_until:
            messages.warning(request, 'Срок прохождения теста истёк.')
            return redirect('tests:tests')
    
    # Проверяем, есть ли уже завершенный результат
    completed_result = TestResult.objects.filter(
        worker=request.user,
        test=test,
        completed_at__isnull=False
    ).first()
    
    if completed_result:
        messages.info(request, 'Вы уже проходили этот тест. Результат сохранен.')
        return redirect('tests:result', result_id=completed_result.id)
    
    # Проверяем лимит попыток
    if test.max_attempts and test.max_attempts > 0:
        attempts_count = TestResult.objects.filter(
            worker=request.user,
            test=test
        ).count()
        if attempts_count >= test.max_attempts:
            messages.warning(request, f'Достигнут лимит попыток для этого теста (макс. {test.max_attempts}).')
            last_result = TestResult.objects.filter(
                worker=request.user,
                test=test,
                completed_at__isnull=False
            ).order_by('-completed_at').first()
            if last_result:
                return redirect('tests:result', result_id=last_result.id)
            return redirect('tests:tests')
    
    # Удаляем все незавершенные попытки
    TestResult.objects.filter(
        worker=request.user,
        test=test,
        completed_at__isnull=True
    ).delete()
    
    # Создаем новую запись о начале теста
    result = TestResult.objects.create(
        worker=request.user,
        test=test,
        started_at=timezone.now()
    )
    
    # Перенаправляем на страницу теста с GET-параметром result_id
    from django.urls import reverse
    url = reverse('tests:detail', args=[test.id]) + f'?result_id={result.id}'
    return redirect(url)

@login_required
def take_test(request, result_id):
    """Прохождение теста"""
    result = get_object_or_404(TestResult, id=result_id, worker=request.user)
    
    # Если тест уже завершен
    if result.completed_at:
        messages.info(request, 'Тест уже завершен. Просмотрите результат.')
        return redirect('tests:result', result_id=result.id)
    
    test = result.test
    questions = test.questions.all()
    
    if request.method == 'POST':
        # Обработка ответов (как обычно)
        score = 0
        total_points = 0
        
        for question in questions:
            total_points += question.points
            # ... логика обработки ответов ...
        
        percentage = (score / total_points * 100) if total_points > 0 else 0
        passed = percentage >= test.passing_score
        
        result.score = score
        result.percentage = percentage
        result.passed = passed
        result.completed_at = timezone.now()
        result.time_taken = (result.completed_at - result.started_at).seconds
        result.save()
        
        messages.success(request, f'Тест завершен! Ваш результат: {percentage:.1f}%')
        return redirect('tests:result', result_id=result.id)
    
    context = {
        'test': test,
        'questions': questions,
        'result': result,
    }
    return render(request, 'tests/test_detail.html', context)

@login_required
def test_result(request, result_id):
    result = get_object_or_404(TestResult, id=result_id)
    
   
    if result.worker != request.user and not request.user.is_moderator:
        messages.error(request, 'Доступ запрещен')
        return redirect('tests:tests')
    
    # Вычисляем минуты и секунды
    if result.time_taken:
        minutes = result.time_taken // 60
        seconds = result.time_taken % 60
    else:
        minutes = 0
        seconds = 0
    

    user_answers = result.answers.all().select_related('question').prefetch_related('selected_answers')
    
    detailed_answers = []
    for ua in user_answers:
        question = ua.question
        correct_answers = question.answers.filter(is_correct=True)
        
        # Для текстовых вопросов
        text_answer = ua.text_answer if hasattr(ua, 'text_answer') else None
        
        detailed_answers.append({
            'question': question,
            'user_answers': ua.selected_answers.all(),
            'correct_answers': correct_answers,
            'is_correct': ua.is_correct,
            'text_answer': text_answer,  # Добавляем текстовый ответ
        })
    
    context = {
        'result': result,
        'detailed_answers': detailed_answers,
        'minutes': minutes,
        'seconds': seconds,
    }
    return render(request, 'tests/test_result.html', context)


# ========== ПРОБНЫЕ ТЕСТЫ ==========

@login_required
def trial_page(request, test_id):
    """Страница пробного теста"""
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    if not test.is_trial:
        messages.warning(request, 'Это не пробный тест.')
        return redirect('tests:detail', test_id=test_id)
    
    trial_attempts = request.session.get('trial_attempts', {})
    used = trial_attempts.get(str(test_id), 0)
    
    context = {
        'test': test,
        'used_attempts': used,
        'max_attempts': 2,
    }
    return render(request, 'tests/trial_intro.html', context)


@login_required
def trial_start(request, test_id):
    """Начать пробный тест"""
    if request.method != 'POST':
        return redirect('tests:trial_page', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    if not test.is_trial:
        return redirect('tests:detail', test_id=test_id)
    
    trial_attempts = request.session.get('trial_attempts', {})
    used = trial_attempts.get(str(test_id), 0)
    
    if used >= 2:
        messages.warning(request, 'Достигнут лимит попыток для пробного теста (2 попытки).')
        return redirect('tests:trial_page', test_id=test_id)
    
    trial_attempts[str(test_id)] = used + 1
    request.session['trial_attempts'] = trial_attempts
    request.session['trial_test_id'] = test_id
    
    return redirect('tests:trial_take', test_id=test_id)


@login_required
def trial_take(request, test_id):
    """Страница прохождения пробного теста"""
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    if not test.is_trial or request.session.get('trial_test_id') != test_id:
        messages.warning(request, 'Начните пробный тест со страницы теста.')
        return redirect('tests:trial_page', test_id=test_id)
    
    questions = test.questions.all()
    
    if not questions:
        messages.warning(request, 'В тесте нет вопросов.')
        return redirect('tests:trial_page', test_id=test_id)
    
    context = {
        'test': test,
        'questions': questions,
    }
    return render(request, 'tests/trial_take.html', context)


@login_required
def trial_submit(request, test_id):
    """Отправить ответы пробного теста"""
    if request.method != 'POST':
        return redirect('tests:trial_page', test_id=test_id)
    
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    if not test.is_trial:
        return redirect('tests:detail', test_id=test_id)
    
    request.session.pop('trial_test_id', None)
    
    questions = test.questions.all()
    score = 0
    total_points = sum(q.points for q in questions)
    detailed_answers = []
    
    for question in questions:
        is_correct = False
        user_answers = []
        correct_answers = list(question.answers.filter(is_correct=True))
        text_answer = None
        
        if question.question_type == 'single':
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    answer = Answer.objects.get(id=int(answer_id))
                    user_answers = [answer]
                    is_correct = answer.is_correct
                    if is_correct:
                        score += question.points
                except (ValueError, Answer.DoesNotExist):
                    pass
        
        elif question.question_type == 'multiple':
            answer_ids = request.POST.getlist(f'question_{question.id}')
            if answer_ids:
                answer_ids = [int(a) for a in answer_ids]
                user_answers = Answer.objects.filter(id__in=answer_ids)
                correct_ids = [a.id for a in correct_answers]
                is_correct = (set(answer_ids) == set(correct_ids))
                if is_correct:
                    score += question.points
        
        elif question.question_type == 'text':
            text_answer = request.POST.get(f'question_text_{question.id}', '').strip()
            if text_answer and correct_answers:
                is_correct = (text_answer.lower() == correct_answers[0].text.lower())
                if is_correct:
                    score += question.points
        
        detailed_answers.append({
            'question': question,
            'user_answers': user_answers,
            'correct_answers': correct_answers,
            'is_correct': is_correct,
            'text_answer': text_answer
        })
    
    percentage = (score / total_points * 100) if total_points > 0 else 0
    passed = percentage >= test.passing_score
    
    context = {
        'test': test,
        'score': score,
        'total_points': total_points,
        'percentage': percentage,
        'passed': passed,
        'detailed_answers': detailed_answers,
    }
    return render(request, 'tests/trial_result.html', context)