from django import forms

from apps.accounts.models import PrayerRequest, Testimony
from apps.articles.models import Article
from apps.devotions.models import Devotion
from apps.podcasts.models import Episode
from apps.videos.models import Video


class ArticleContentForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title_en", "title_rw", "hook_en", "hook_rw",
            "body_en", "body_rw",
            "verse_text_en", "verse_text_rw", "verse_ref_en", "verse_ref_rw",
            "author", "cover_image", "icon", "color",
        ]
        widgets = {
            "body_en": forms.Textarea(attrs={"rows": 8}),
            "body_rw": forms.Textarea(attrs={"rows": 8}),
        }


class DevotionContentForm(forms.ModelForm):
    class Meta:
        model = Devotion
        fields = [
            "date", "verse_ref", "verse_text_en", "verse_text_rw",
            "reflection_en", "reflection_rw", "prayer_en", "prayer_rw",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class EpisodeContentForm(forms.ModelForm):
    class Meta:
        model = Episode
        fields = [
            "series", "title_en", "title_rw", "description_en", "description_rw",
            "duration", "audio_url", "audio_file", "order",
        ]


class VideoContentForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["series", "title_en", "title_rw", "youtube_url", "order"]


# Shared registry so admin review views and author create/edit views can both
# work generically across the four reviewable content types.
CONTENT_REGISTRY = {
    "article": {"model": Article, "form": ArticleContentForm, "label": "Article"},
    "devotion": {"model": Devotion, "form": DevotionContentForm, "label": "Devotion"},
    "episode": {"model": Episode, "form": EpisodeContentForm, "label": "Podcast episode"},
    "video": {"model": Video, "form": VideoContentForm, "label": "Video"},
}


class TestimonyForm(forms.ModelForm):
    class Meta:
        model = Testimony
        fields = ["title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 6})}


class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class RejectContentForm(forms.Form):
    review_note = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Reason for rejection",
        help_text="The author will see this note and can resubmit.",
    )


class UserRoleForm(forms.Form):
    role = forms.ChoiceField(choices=[("member", "Member"), ("author", "Author")])
