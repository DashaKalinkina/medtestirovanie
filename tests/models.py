from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User

class TestCategory(models.Model):
    """Категория тестов"""
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)  # Добавьте эту строку

    class Meta:
        verbose_name = 'Категория теста'
        verbose_name_plural = 'Категории тестов'
        ordering = ['name']

    def __str__(self):
        return self.name


class Test(models.Model):
    """Модель теста"""
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Легкий'
        MEDIUM = 'medium', 'Средний'
        HARD = 'hard', 'Сложный'

    class AccessType(models.TextChoices):
        SIMPLE = 'simple', 'Обычный'
        SUBSCRIBED = 'subscribed', 'По подписке'

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(
        TestCategory, on_delete=models.SET_NULL, null=True,
        related_name='tests', verbose_name='Категория'
    )
    difficulty = models.CharField(
        'Сложность', max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    time_limit = models.IntegerField('Лимит времени (сек)', default=3600)
    passing_score = models.IntegerField('Проходной балл (%)', default=70)

    access_type = models.CharField(
        'Тип доступа', max_length=20, choices=AccessType.choices, default=AccessType.SIMPLE
    )
    max_attempts = models.IntegerField('Максимум попыток', default=1, help_text='0 - без ограничений')
    start_at = models.DateTimeField('Начало доступа', null=True, blank=True)
    end_at = models.DateTimeField('Окончание доступа', null=True, blank=True)

    is_strict_mode = models.BooleanField('Строгий режим', default=True)
    shuffle_questions = models.BooleanField('Перемешивать вопросы', default=False)
    shuffle_answers = models.BooleanField('Перемешивать ответы', default=False)

    is_trial = models.BooleanField('Пробный тест', default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_tests'
    )
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class TestSubscription(models.Model):
    """Подписка пользователя на тест"""
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_subscriptions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed_at = models.DateTimeField('Дата подписки', auto_now_add=True)
    valid_from = models.DateTimeField('Доступен с', default=timezone.now)
    valid_until = models.DateTimeField('Доступен до', null=True, blank=True)

    class Meta:
        verbose_name = 'Подписка на тест'
        verbose_name_plural = 'Подписки на тесты'
        unique_together = ['worker', 'test']

    def __str__(self):
        return f"{self.worker} - {self.test}"


class Question(models.Model):
    """Вопрос теста"""
    class QuestionType(models.TextChoices):
        SINGLE = 'single', 'Один вариант'
        MULTIPLE = 'multiple', 'Несколько вариантов'
        TEXT = 'text', 'Текстовый ответ'

    class Level(models.TextChoices):
        BASIC = 'basic', 'Базовый'
        MEDIUM = 'medium', 'Средний'
        HARD = 'hard', 'Сложный'

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField('Текст вопроса')
    question_type = models.CharField(
        'Тип вопроса', max_length=20, choices=QuestionType.choices, default=QuestionType.SINGLE
    )
    points = models.IntegerField('Баллы', default=1)
    image = models.ImageField('Изображение', upload_to='questions/', null=True, blank=True)
    topic = models.CharField('Тема', max_length=200, blank=True)
    question_level = models.CharField(
        'Уровень', max_length=20, choices=Level.choices, default=Level.MEDIUM
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)
    last_modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='modified_questions'
    )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['test', 'id']

    def __str__(self):
        return f"{self.test.title} - {self.text[:50]}"


class Answer(models.Model):
    """Вариант ответа"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField('Текст ответа')
    is_correct = models.BooleanField('Правильный', default=False)

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'

    def __str__(self):
        return f"{self.question.text[:30]} - {self.text[:30]}"


class TestResult(models.Model):
    """Результат прохождения теста"""
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField('Баллы', default=0)
    percentage = models.FloatField('Процент', default=0)
    passed = models.BooleanField('Сдано', default=False)
    started_at = models.DateTimeField('Начало', default=timezone.now)
    completed_at = models.DateTimeField('Завершено', null=True, blank=True)
    time_taken = models.IntegerField('Затрачено времени (сек)', null=True, blank=True)

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.worker} - {self.test} - {self.percentage}%"


class UserAnswer(models.Model):
    """Ответ пользователя на конкретный вопрос"""
    result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    text_answer = models.TextField('Текстовый ответ', blank=True)
    is_correct = models.BooleanField('Правильно', default=False)

    class Meta:
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'

    def __str__(self):
        return f"Ответ {self.result.worker} на {self.question}"