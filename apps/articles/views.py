from django.shortcuts import get_object_or_404, render

from .models import Article


def article_list(request):
    articles = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by("-is_featured", "-published_at")
    return render(request, "articles/article_list.html", {"articles": articles})


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status=Article.STATUS_PUBLISHED)
    is_bookmarked = (
        request.user.is_authenticated
        and article.bookmarked_by.filter(member=request.user).exists()
    )
    return render(request, "articles/article_detail.html", {
        "article": article,
        "related_articles": article.related_articles(),
        "is_bookmarked": is_bookmarked,
    })
