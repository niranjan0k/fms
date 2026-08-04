from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EmployeeCreateForm
from .models import User

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
            messages.success(request, "User created.")
            return redirect("user_list")
    else:
        form = EmployeeCreateForm()
    return render(request, "accounts/user_form.html", {"form": form})
