from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User


class LoginForm(forms.Form):
    """Форма входа"""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    remember = forms.BooleanField(
        label='Запомнить меня',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            from django.contrib.auth import authenticate
            self.user = authenticate(username=email, password=password)
            
            if self.user is None:
                raise ValidationError('Неверный email или пароль')
            elif not self.user.is_active:
                raise ValidationError('Ваш аккаунт деактивирован')
        
        return self.cleaned_data
    
    def get_user(self):
        return getattr(self, 'user', None)


class RegistrationForm(UserCreationForm):
    """Форма регистрации"""
    
    SPECIALIZATIONS = [
         ('doctor', 'Врач'),
    ('nurse', 'Медсестра/медбрат'),
    ('paramedic', 'Фельдшер'),
    ('intern', 'Интерн'),
    ]
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    specialization = forms.ChoiceField(
        label='Специализация',
        choices=SPECIALIZATIONS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    license_number = forms.CharField(
        label='Номер лицензии',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите номер лицензии'
        })
    )
    institution = forms.CharField(
        label='Медицинское учреждение',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название учреждения'
        })
    )
    position = forms.CharField(
        label='Должность',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите должность'
        })
    )
    years_experience = forms.IntegerField(
        label='Стаж работы (лет)',
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите стаж'
        })
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'specialization', 'license_number', 'institution',
            'position', 'years_experience', 'password1', 'password2'
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        return username
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if User.objects.filter(license_number=license_number).exists():
            raise ValidationError('Медицинский работник с таким номером лицензии уже существует')
        return license_number
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user
    
 
class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'specialization', 
            'institution', 'position', 'years_experience',
            'email_notifications'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={'class': 'form-input'}),
            'position': forms.TextInput(attrs={'class': 'form-input'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }   