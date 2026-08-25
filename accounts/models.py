from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),  # kompaniya admini
        ('operator', 'Operator'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        ordering = ['username']
