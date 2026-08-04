from django import forms
from .models import Letter
from apps.accounts.models import User, Role

class LetterCreateForm(forms.ModelForm):
    class Meta:
        model = Letter
        fields = ("title", "description", "attachment")

class ForwardForm(forms.Form):
    to_user = forms.ModelChoiceField(queryset=User.objects.none())
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, actor, letter, **kwargs):
        super().__init__(*args, **kwargs)
        qs = User.objects.exclude(pk=actor.pk)
        if actor.is_director:
            # A Director starts the employee route at level 1, or sends to Minister.
            qs = qs.filter(role=Role.MINISTER) | qs.filter(role=Role.EMPLOYEE, level=1)
        elif actor.is_minister:
            qs = qs.filter(role=Role.DIRECTOR)
        elif actor.is_employee:
            # An employee may return to Director or forward only to the next level.
            qs = qs.filter(role=Role.DIRECTOR) | qs.filter(role=Role.EMPLOYEE, level=actor.level + 1)
        self.fields["to_user"].queryset = qs.order_by("role", "level", "username")

class CommentOnlyForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
