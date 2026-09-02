from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Profile


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(required=True, max_length=150)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False, max_length=40)
    preferred_language = forms.ChoiceField(choices=Profile.LANGUAGE_CHOICES, initial=Profile.LANGUAGE_EN)
    privacy_accepted = forms.BooleanField(
        required=True,
        label="I agree to the privacy policy and terms.",
    )
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "email",
            "phone_number",
            "preferred_language",
            "password1",
            "password2",
            "privacy_accepted",
            "website",
        ]

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("We could not process this submission. Please try again.")
        return ""

    def clean_privacy_accepted(self):
        if not self.cleaned_data.get("privacy_accepted"):
            raise forms.ValidationError("Please accept the privacy policy to continue.")
        return True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
            profile = user.profile
            profile.full_name = self.cleaned_data["full_name"]
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.preferred_language = self.cleaned_data["preferred_language"]
            profile.privacy_accepted_at = timezone.now()
            profile.privacy_policy_version = "2026-09-01"
            profile.save()
        return user
