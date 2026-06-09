from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import UserManager


class User(AbstractUser):
    """Медицинский работник - расширенная модель пользователя"""
    
    # Роли
    class Role(models.TextChoices):
        WORKER = 'worker', 'Медицинский работник'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'
    
    # Основные поля (переопределяем для явного указания)
    email = models.EmailField('Email', unique=True)
    username = models.CharField('Имя пользователя', max_length=80, unique=True)
    first_name = models.CharField('Имя', max_length=80)
    last_name = models.CharField('Фамилия', max_length=80)
    
    # Специализация и квалификация
    specialization = models.CharField('Специализация', max_length=50)
    license_number = models.CharField('Номер лицензии', max_length=50, unique=True)
    institution = models.CharField('Учреждение', max_length=200, blank=True)
    position = models.CharField('Должность', max_length=100, blank=True)
    years_experience = models.IntegerField('Стаж (лет)', default=0, 
                                          validators=[MinValueValidator(0)])
    
    # Роли и права
    is_moderator = models.BooleanField('Модератор', default=False)
    is_admin = models.BooleanField('Администратор', default=False)
    
    # role поле
    role = models.CharField('Роль', max_length=20, 
                           choices=Role.choices, 
                           default=Role.WORKER)
    
    # Метаданные
    created_at = models.DateTimeField('Дата регистрации', default=timezone.now)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Настройки пользователя
    email_notifications = models.BooleanField('Email уведомления', default=True)
    
    # Используем стандартный менеджер
    objects = UserManager()
    
    # Поле для аутентификации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'specialization', 'license_number']
    
    class Meta:
        verbose_name = 'Медицинский работник'
        verbose_name_plural = 'Медицинские работники'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Полное имя пользователя"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Короткое имя"""
        return self.first_name
    
    @property
    def is_admin_user(self):
        """Проверка, является ли пользователь администратором"""
        return self.is_admin or self.is_superuser
    
    def has_subscription_to_test(self, test):
        """Проверяет, есть ли у пользователя подписка на тест"""
        return self.test_subscriptions.filter(
            test=test,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        ).exists()