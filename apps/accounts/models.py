from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    MINISTER = "MINISTER", "Minister"
    DIRECTOR = "DIRECTOR", "Director (Super Admin)"
    EMPLOYEE = "EMPLOYEE", "Next Level Employee"

class User(AbstractUser):
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.EMPLOYEE)
    level = models.PositiveIntegerField(null=True, blank=True,
        help_text="Order in employee chain (1,2,3...). Required for EMPLOYEE role.")

    @property
    def is_director(self): return self.role == Role.DIRECTOR
    @property
    def is_minister(self): return self.role == Role.MINISTER
    @property
    def is_employee(self): return self.role == Role.EMPLOYEE

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
