from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from chat.models import Message

# from chat.core.models.conversation import Conversation


class User(AbstractUser):

    last_read_date = models.DateTimeField(
        auto_now_add=True,
        blank=False,
        null=False
    )
    online = models.BooleanField(null=False, blank=False, default=False)

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def read(self):
        self.last_read_date = timezone.now()
        self.save()

    def unread_messages(self):
        return Message.objects.filter(created_at__gt=self.last_read_date) \
                              .count()