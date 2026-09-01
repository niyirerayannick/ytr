from django import forms

from .models import ContactMessage, NewsletterSubscriber


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"required": True}),
            "email": forms.EmailInput(attrs={"required": True}),
            "message": forms.Textarea(attrs={"required": True}),
        }


class NewsletterSubscriberForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        return email

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        obj, _created = NewsletterSubscriber.objects.get_or_create(email=email)
        return obj
