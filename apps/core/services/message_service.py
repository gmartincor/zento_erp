from django.contrib import messages
from apps.core.constants import SUCCESS_MESSAGES, ERROR_MESSAGES

class MessageService:
    @staticmethod
    def success(request, key, **kwargs):
        message = SUCCESS_MESSAGES.get(key, key)
        if kwargs:
            message = message.format(**kwargs)
        messages.success(request, message)
        
    @staticmethod
    def error(request, key, **kwargs):
        message = ERROR_MESSAGES.get(key, key)
        if kwargs:
            message = message.format(**kwargs)
        messages.error(request, message)
    
    @staticmethod
    def info(request, message):
        messages.info(request, message)
    
    @staticmethod
    def warning(request, message):
        messages.warning(request, message)
