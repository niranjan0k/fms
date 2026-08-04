from django.db import models
from django.conf import settings

class Movement(models.Model):
    ACTIONS = [("CREATE","Create"),("FORWARD","Forward"),("RETURN","Return"),("COMPLETE","Complete")]
    letter = models.ForeignKey("letters.Letter", on_delete=models.CASCADE, related_name="movements")
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="moves_from")
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="moves_to")
    action = models.CharField(max_length=16, choices=ACTIONS)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["letter", "created_at"])]

class Comment(models.Model):
    letter = models.ForeignKey("letters.Letter", on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
