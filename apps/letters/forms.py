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
            qs = qs.filter(role__in=[Role.MINISTER, Role.EMPLOYEE])
        elif actor.is_minister:
            qs = qs.filter(role=Role.DIRECTOR)
        elif actor.is_employee:
            # forward to next employee level or back to director
            qs = qs.filter(role__in=[Role.EMPLOYEE, Role.DIRECTOR])
        self.fields["to_user"].queryset = qs.order_by("role", "level", "username")

class CommentOnlyForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
