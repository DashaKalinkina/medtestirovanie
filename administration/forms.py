from django import forms
from tests.models import Test, TestCategory, Question

class TestForm(forms.ModelForm):
    """Форма создания/редактирования теста"""
    
    title = forms.CharField(
        label='Название теста',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название теста'})
    )
    description = forms.CharField(
        label='Описание теста',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишите тест...'})
    )
    category = forms.ModelChoiceField(
        label='Категория',
        queryset=TestCategory.objects.all(),
        required=False,
        empty_label='— Без категории —',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    difficulty = forms.ChoiceField(
        label='Сложность',
        choices=[('easy', 'Легкий'), ('medium', 'Средний'), ('hard', 'Сложный')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    time_limit = forms.IntegerField(
        label='Лимит времени (минут)',
        initial=60,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    passing_score = forms.IntegerField(
        label='Проходной балл (%)',
        initial=70,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    access_type = forms.ChoiceField(
        label='Тип доступа',
        choices=[
            ('simple', 'Обычный тест (сразу доступен)'),
            ('subscribed', 'Тест по подписке (нужно записаться)'),
        ],
        initial='simple',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    max_attempts = forms.IntegerField(
        label='Максимум попыток',
        initial=1,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    is_trial = forms.BooleanField(
        label='Пробный тест (максимум 2 попытки)',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Test
        fields = ['title', 'description', 'category', 'difficulty', 'time_limit', 
                  'passing_score', 'access_type', 'max_attempts', 'is_trial']


class CategoryForm(forms.ModelForm):
    """Форма для создания/редактирования категории"""
    
    class Meta:
        model = TestCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название категории'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Описание (необязательно)'}),
        }


class QuestionForm(forms.Form):
    """Форма для вопроса"""
    question_text = forms.CharField(
        label='Текст вопроса',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    question_type = forms.ChoiceField(
        label='Тип вопроса',
        choices=[
            ('single', 'Один правильный ответ'),
            ('multiple', 'Несколько правильных ответов'),
            ('text', 'Текстовый ответ (слово/фраза)')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    points = forms.IntegerField(
        label='Баллы',
        initial=1,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    topic = forms.CharField(
        label='Тема / раздел',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Кардиология, Вакцинация детей...'})
    )
    question_level = forms.ChoiceField(
        label='Уровень сложности вопроса',
        choices=[
            ('basic', 'Базовый'),
            ('medium', 'Средний'),
            ('hard', 'Сложный')
        ],
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-select'})
    )