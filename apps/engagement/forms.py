from django import forms

from .models import ContactMessage, NewsletterSubscriber


class ContactMessageForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"required": True}),
            "email": forms.EmailInput(attrs={"required": True}),
            "message": forms.Textarea(attrs={"required": True}),
        }

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("We could not process this submission. Please try again.")
        return ""


class NewsletterSubscriberForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        return email

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise forms.ValidationError("We could not process this submission. Please try again.")
        return ""

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        obj, _created = NewsletterSubscriber.objects.get_or_create(email=email)
        return obj
