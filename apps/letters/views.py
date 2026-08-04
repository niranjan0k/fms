from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from apps.accounts.models import Role, User
from apps.workflow.models import Movement, Comment
from .forms import LetterCreateForm, ForwardForm, CommentOnlyForm
from .models import Letter, LetterStatus


@login_required
def letter_list(request):
    u = request.user
    qs = Letter.objects.all()
    tab = request.GET.get("tab", "inbox")
    if tab == "inbox":
        qs = qs.filter(current_holder=u).exclude(status=LetterStatus.COMPLETE)
    elif tab == "mine":
        qs = qs.filter(created_by=u)
    elif tab == "all":
        pass  # everyone can view status per POC spec
    all_letters = Letter.objects.all()
    return render(request, "letters/list.html", {
        "letters": qs, "tab": tab,
        "inbox_count": all_letters.filter(current_holder=u).exclude(status=LetterStatus.COMPLETE).count(),
        "open_count": all_letters.exclude(status=LetterStatus.COMPLETE).count(),
        "complete_count": all_letters.filter(status=LetterStatus.COMPLETE).count(),
        "total_count": all_letters.count(),
    })


@login_required
def letter_create(request):
    if not request.user.is_director:
        return HttpResponseForbidden("Only Director can create letters.")
    if request.method == "POST":
        form = LetterCreateForm(request.POST, request.FILES)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.created_by = request.user
            letter.current_holder = request.user
            letter.save()
            # move DRAFT -> WITH_DIRECTOR immediately
            letter.status = LetterStatus.WITH_DIRECTOR
            letter.save()
            Movement.objects.create(letter=letter, from_user=request.user,
                to_user=request.user, action="CREATE", comment="")
            messages.success(request, f"Created {letter.reference_no}")
            return redirect("letter_detail", pk=letter.pk)
    else:
        form = LetterCreateForm()
    return render(request, "letters/form.html", {"form": form})


@login_required
def letter_detail(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    movements = letter.movements.select_related("from_user", "to_user").order_by("created_at")
    comments = letter.comments.select_related("author").order_by("created_at")
    forward_form = ForwardForm(actor=request.user, letter=letter)
    comment_form = CommentOnlyForm()
    can_act = (letter.current_holder_id == request.user.id
               and letter.status != LetterStatus.COMPLETE)
    final_level = User.objects.filter(role=Role.EMPLOYEE).order_by("-level").values_list("level", flat=True).first()
    can_complete = (can_act and request.user.is_employee
                    and letter.status == LetterStatus.WITH_EMPLOYEE
                    and final_level is not None and request.user.level == final_level)
    return render(request, "letters/detail.html", {
        "letter": letter, "movements": movements, "comments": comments,
        "forward_form": forward_form, "comment_form": comment_form,
        "can_act": can_act, "can_complete": can_complete,
    })


@login_required
def letter_forward(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    if letter.current_holder_id != request.user.id:
        return HttpResponseForbidden("Not your letter.")
    if request.method != "POST":
        return redirect("letter_detail", pk=pk)
    form = ForwardForm(request.POST, actor=request.user, letter=letter)
    if not form.is_valid():
        messages.error(request, "Invalid forward.")
        return redirect("letter_detail", pk=pk)
    to_user = form.cleaned_data["to_user"]
    comment = form.cleaned_data["comment"]
    try:
        if to_user.role == Role.MINISTER:
            letter.forward_to_minister(by_user=request.user, to_user=to_user, comment=comment)
        elif to_user.role == Role.DIRECTOR:
            letter.return_to_director(by_user=request.user, to_user=to_user, comment=comment)
        elif to_user.role == Role.EMPLOYEE:
            letter.forward_to_employee(by_user=request.user, to_user=to_user, comment=comment)
        letter.save()
        messages.success(request, f"Forwarded to {to_user}")
    except Exception as e:
        messages.error(request, f"Transition not allowed: {e}")
    return redirect("letter_detail", pk=pk)


@login_required
def letter_complete(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    if letter.current_holder_id != request.user.id:
        return HttpResponseForbidden()
    final_level = User.objects.filter(role=Role.EMPLOYEE).order_by("-level").values_list("level", flat=True).first()
    if not (request.user.is_employee and final_level is not None and request.user.level == final_level):
        return HttpResponseForbidden("Only the final employee level can complete this item.")
    if request.method == "POST":
        try:
            letter.mark_complete(by_user=request.user,
                comment=request.POST.get("comment", ""))
            letter.save()
            messages.success(request, "Marked complete.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect("letter_detail", pk=pk)


@login_required
def letter_comment(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    if request.method == "POST":
        form = CommentOnlyForm(request.POST)
        if form.is_valid():
            Comment.objects.create(letter=letter, author=request.user,
                body=form.cleaned_data["comment"])
            messages.success(request, "Comment added.")
    return redirect("letter_detail", pk=pk)
