from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import EmployeeCreateForm, LevelForm
from .models import User, EmployeeLevel

def _director(u): return u.is_authenticated and u.is_director

@login_required
@user_passes_test(_director)
def user_list(request):
    users = User.objects.all().order_by("role", "level", "username")
    return render(request, "accounts/user_list.html", {"users": users})

@login_required
@user_passes_test(_director)
def user_create(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("user_list")
    else:
        form = EmployeeCreateForm()
    return render(request, "accounts/user_form.html", {"form": form, "editing": False})

@login_required
@user_passes_test(_director)
def level_list(request):
    levels = EmployeeLevel.objects.all()
    return render(request, "accounts/level_list.html", {"levels": levels})

@login_required
@user_passes_test(_director)
def level_create(request):
    if request.method == "POST":
        form = LevelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Level configuration saved.")
            return redirect("level_list")
    else:
        form = LevelForm()
    return render(request, "accounts/level_form.html", {"form": form, "editing": False})

@login_required
@user_passes_test(_director)
def level_edit(request, pk):
    level = get_object_or_404(EmployeeLevel, pk=pk)
    if request.method == "POST":
        form = LevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            messages.success(request, "Level updated.")
            return redirect("level_list")
    else:
        form = LevelForm(instance=level)
    return render(request, "accounts/level_form.html", {"form": form, "editing": True, "level": level})

@login_required
@user_passes_test(_director)
def level_delete(request, pk):
    level = get_object_or_404(EmployeeLevel, pk=pk)
    if request.method == "POST":
        level.delete()
        messages.success(request, f"Level {level.level} removed.")
        return redirect("level_list")
    return render(request, "accounts/level_confirm_delete.html", {"level": level})

@login_required
@user_passes_test(_director)
def role_rights(request):
    rights = [
        {
            "action": "Create letters / orders",
            "director": True, "minister": False, "employee": False,
            "note": "Director only"
        },
        {
            "action": "Forward to Minister",
            "director": True, "minister": False, "employee": False,
            "note": "Director only"
        },
        {
            "action": "Forward to Level 1 Employee",
            "director": True, "minister": False, "employee": False,
            "note": "Director only"
        },
        {
            "action": "Return to Director",
            "director": False, "minister": True, "employee": True,
            "note": "Minister & all employees"
        },
        {
            "action": "Forward to next employee level",
            "director": False, "minister": False, "employee": True,
            "note": "Employee only (sequential)"
        },
        {
            "action": "Mark correspondence complete",
            "director": False, "minister": False, "employee": True,
            "note": "Final-level employee only"
        },
        {
            "action": "Add comments",
            "director": True, "minister": True, "employee": True,
            "note": "All roles"
        },
        {
            "action": "View all correspondence",
            "director": True, "minister": True, "employee": True,
            "note": "All roles (track screen)"
        },
        {
            "action": "View inbox (assigned items)",
            "director": True, "minister": True, "employee": True,
            "note": "All roles"
        },
        {
            "action": "Create & manage user accounts",
            "director": True, "minister": False, "employee": False,
            "note": "Director (Super Admin) only"
        },
        {
            "action": "Configure employee levels",
            "director": True, "minister": False, "employee": False,
            "note": "Director (Super Admin) only"
        },
        {
            "action": "View reports & statistics",
            "director": True, "minister": False, "employee": False,
            "note": "Director only"
        },
    ]
    return render(request, "accounts/role_rights.html", {"rights": rights})
