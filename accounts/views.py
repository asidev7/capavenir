from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from orientation.models import OrientationSession

from .forms import AvatarForm, ProfileForm
from .models import Profile


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        avatar_form = AvatarForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid() and avatar_form.is_valid():
            form.save()
            avatar_form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)
        avatar_form = AvatarForm(instance=request.user)
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "avatar_form": avatar_form, "profile": profile},
    )


@login_required
def my_reports(request):
    sessions = (
        OrientationSession.objects.filter(user=request.user)
        .select_related("report")
        .order_by("-created_at")
    )
    return render(request, "accounts/my_reports.html", {"sessions": sessions})
