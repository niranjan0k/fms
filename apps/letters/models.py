import uuid
from django.db import models, connection
from django.conf import settings
from django.utils import timezone
from django_fsm import FSMField, transition

class LetterStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    WITH_DIRECTOR = "WITH_DIRECTOR", "With Director"
    WITH_MINISTER = "WITH_MINISTER", "With Minister"
    WITH_EMPLOYEE = "WITH_EMPLOYEE", "With Employee"
    COMPLETE = "COMPLETE", "Complete"

def _next_ref_no():
    with connection.cursor() as c:
        c.execute("CREATE SEQUENCE IF NOT EXISTS letter_ref_seq START 1;")
        c.execute("SELECT nextval('letter_ref_seq');")
        seq = c.fetchone()[0]
    return f"FMS/{timezone.now().year}/{seq:06d}"

class Letter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_no = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="letters/%Y/%m/", blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, related_name="letters_created")
    current_holder = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, related_name="letters_holding")

    status = FSMField(default=LetterStatus.DRAFT, choices=LetterStatus.choices, protected=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["current_holder"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = _next_ref_no()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_no} — {self.title}"

    # ---- transitions ----
    @transition(field=status, source=[LetterStatus.DRAFT, LetterStatus.WITH_MINISTER, LetterStatus.WITH_EMPLOYEE],
                target=LetterStatus.WITH_DIRECTOR)
    def return_to_director(self, by_user, to_user, comment=""):
        self._log(by_user, to_user, "RETURN", comment)
        self.current_holder = to_user

    @transition(field=status, source=LetterStatus.WITH_DIRECTOR, target=LetterStatus.WITH_MINISTER)
    def forward_to_minister(self, by_user, to_user, comment=""):
        self._log(by_user, to_user, "FORWARD", comment)
        self.current_holder = to_user

    @transition(field=status, source=[LetterStatus.WITH_DIRECTOR, LetterStatus.WITH_EMPLOYEE],
                target=LetterStatus.WITH_EMPLOYEE)
    def forward_to_employee(self, by_user, to_user, comment=""):
        self._log(by_user, to_user, "FORWARD", comment)
        self.current_holder = to_user

    @transition(field=status, source=LetterStatus.WITH_EMPLOYEE, target=LetterStatus.COMPLETE)
    def mark_complete(self, by_user, comment=""):
        self._log(by_user, by_user, "COMPLETE", comment)

    def _log(self, by_user, to_user, action, comment):
        from apps.workflow.models import Movement
        Movement.objects.create(
            letter=self, from_user=by_user, to_user=to_user,
            action=action, comment=comment or "",
        )
