from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
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
    tab = request.GET.get("tab", "all")
    if tab == "mine":
        qs = qs.filter(created_by=u)
    elif tab == "all":
        pass
    all_letters = Letter.objects.all()
    return render(request, "letters/list.html", {
        "letters": qs, "tab": tab,
        "inbox_count": all_letters.filter(current_holder=u).exclude(status=LetterStatus.COMPLETE).count(),
        "open_count": all_letters.exclude(status=LetterStatus.COMPLETE).count(),
        "complete_count": all_letters.filter(status=LetterStatus.COMPLETE).count(),
        "total_count": all_letters.count(),
    })

@login_required
def letter_inbox(request):
    u = request.user
    qs = Letter.objects.filter(current_holder=u).exclude(status=LetterStatus.COMPLETE)
    all_letters = Letter.objects.all()
    return render(request, "letters/inbox.html", {
        "letters": qs,
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
            # Move DRAFT → WITH_DIRECTOR via the allowed transition
            director = request.user
            letter.return_to_director(by_user=director, to_user=director, comment="")
            letter.save()
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


def _director(u): return u.is_authenticated and u.is_director

@login_required
@user_passes_test(_director)
def reports(request):
    from apps.workflow.models import Movement
    total = Letter.objects.count()
    by_status = {
        "With Director": Letter.objects.filter(status=LetterStatus.WITH_DIRECTOR).count(),
        "With Minister": Letter.objects.filter(status=LetterStatus.WITH_MINISTER).count(),
        "With Employee": Letter.objects.filter(status=LetterStatus.WITH_EMPLOYEE).count(),
        "Complete": Letter.objects.filter(status=LetterStatus.COMPLETE).count(),
        "Draft": Letter.objects.filter(status=LetterStatus.DRAFT).count(),
    }
    by_creator = (
        Letter.objects.values("created_by__first_name", "created_by__last_name", "created_by__username")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    recent_movements = (
        Movement.objects.select_related("letter", "from_user", "to_user")
        .order_by("-created_at")[:15]
    )
    recent_letters = Letter.objects.select_related("created_by", "current_holder").order_by("-created_at")[:10]
    return render(request, "letters/reports.html", {
        "total": total,
        "by_status": by_status,
        "by_creator": by_creator,
        "recent_movements": recent_movements,
        "recent_letters": recent_letters,
        "open_count": Letter.objects.exclude(status=LetterStatus.COMPLETE).count(),
        "complete_count": Letter.objects.filter(status=LetterStatus.COMPLETE).count(),
    })
