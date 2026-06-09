from django.contrib.auth.password_validation import (
    MinimumLengthValidator as DjangoMinimumLengthValidator,
    CommonPasswordValidator as DjangoCommonPasswordValidator,
    NumericPasswordValidator as DjangoNumericPasswordValidator,
    UserAttributeSimilarityValidator as DjangoUserAttributeSimilarityValidator,
)



class CustomCommonPasswordValidator(DjangoCommonPasswordValidator):
    """Валидатор распространенных паролей с кастомным сообщением"""
    
    def get_error_message(self):
        return "Этот пароль слишком простой. Придумайте более сложный."
    
    def get_help_text(self):
        return "Пароль не должен быть слишком простым и распространенным."
