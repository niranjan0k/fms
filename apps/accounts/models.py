from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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

    def clean(self):
        super().clean()
        if self.role == Role.EMPLOYEE and not self.level:
            raise ValidationError({"level": "Employee users must have a workflow level."})
        if self.role != Role.EMPLOYEE and self.level:
            raise ValidationError({"level": "Only employee users should have a workflow level."})

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class EmployeeLevel(models.Model):
    level = models.PositiveIntegerField(unique=True, help_text="Workflow chain position (1 = first, highest = final approver).")
    name = models.CharField(max_length=100, help_text="Descriptive name for this level, e.g. 'Initial Review'.")
    description = models.TextField(blank=True, help_text="Optional details about this level's responsibilities.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return f"Level {self.level} — {self.name}"
