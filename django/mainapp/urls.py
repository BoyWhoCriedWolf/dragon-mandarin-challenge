from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.urls import re_path, path, include

from mainapp.views.api.article_reader import ArticleReaderAPIView, ReaderFeedbackAPIView
from mainapp.views.core import IndexView
from mainapp.views.articles import ArticleDetailView, ArticleLoadingView

def trigger_500(request):
    return 1 / 0

def trigger_404(request):
    raise Http404

def author_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    # Like the builtin login_required, except also tests user.is_author
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_author,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


urlpatterns = [

    # API endpoints
    path('api/v0/reader/articles/<int:pk>', ArticleReaderAPIView.as_view(), name='api_article_reader'),
    path('api/v0/reader/feedback', ReaderFeedbackAPIView.as_view(), name='api_reader_feedback'),

    # Simple pages
    path('', IndexView.as_view(), name='index'),

    # Articles
    path('articles/<slug:uuid>', ArticleDetailView.as_view(), name='article_detail'),
    path('articles/loading/<slug:uuid>', ArticleLoadingView.as_view(), name='article_loading'),

]
if settings.ENVIRONMENT == 'dev':
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
