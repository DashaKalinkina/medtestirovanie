from django import forms
from .models import Test, TestCategory

DIFFICULTY_CHOICES = [
    ('easy', 'Легкий'),
    ('medium', 'Средний'),
    ('hard', 'Сложный'),
]

ACCESS_TYPE_CHOICES = [
    ('simple', 'Обычный тест (сразу доступен)'),
    ('subscribed', 'Тест по подписке (нужно записаться)'),
]


class TestForm(forms.ModelForm):
    """Форма создания/редактирования теста (адаптированная из Flask)"""
    
    title = forms.CharField(
        label='Название теста',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название теста'
        })
    )
    description = forms.CharField(
        label='Описание теста',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Введите описание теста'
        })
    )
    category_id = forms.ModelChoiceField(
        label='Категория',
        queryset=TestCategory.objects.all(),
        required=False,
        empty_label='Выберите категорию',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    difficulty = forms.ChoiceField(
        label='Сложность',
        choices=DIFFICULTY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    time_limit = forms.IntegerField(
        label='Лимит времени (минут)',
        initial=60,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    passing_score = forms.IntegerField(
        label='Проходной балл (%)',
        initial=70,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    access_type = forms.ChoiceField(
        label='Тип доступа к тесту',
        choices=ACCESS_TYPE_CHOICES,
        initial='simple',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    max_attempts = forms.IntegerField(
        label='Максимум попыток',
        initial=1,
        min_value=0,
        help_text='0 - без ограничений',
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    is_trial = forms.BooleanField(
        label='Пробный тест (максимум 2 попытки)',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    shuffle_questions = forms.BooleanField(
        label='Перемешивать вопросы',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    shuffle_answers = forms.BooleanField(
        label='Перемешивать ответы',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    is_strict_mode = forms.BooleanField(
        label='Строгий режим (нельзя возвращаться к вопросам)',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = Test
        fields = [
            'title', 'description', 'category', 'difficulty',
            'time_limit', 'passing_score', 'access_type',
            'max_attempts', 'is_trial', 'shuffle_questions',
            'shuffle_answers', 'is_strict_mode'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переименовываем поле category_id обратно в category для совместимости с моделью
        self.fields['category'] = self.fields.pop('category_id')
        
    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        
        # Если это пробный тест, устанавливаем max_attempts = 2
        if cleaned_data.get('is_trial'):
            cleaned_data['max_attempts'] = 2
            
        return cleaned_data


class QuestionForm(forms.Form):
    """Форма для создания вопроса (можно использовать в админке)"""
    text = forms.CharField(
        label='Текст вопроса',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )
    question_type = forms.ChoiceField(
        label='Тип вопроса',
        choices=[
            ('single', 'Один вариант'),
            ('multiple', 'Несколько вариантов'),
            ('text', 'Текстовый ответ'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    points = forms.IntegerField(
        label='Баллы',
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    topic = forms.CharField(
        label='Тема',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    question_level = forms.ChoiceField(
        label='Уровень',
        choices=[
            ('basic', 'Базовый'),
            ('medium', 'Средний'),
            ('hard', 'Сложный'),
        ],
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class AnswerForm(forms.Form):
    """Форма для создания ответа"""
    text = forms.CharField(
        label='Текст ответа',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    is_correct = forms.BooleanField(
        label='Правильный ответ',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    order = forms.IntegerField(
        label='Порядок',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )