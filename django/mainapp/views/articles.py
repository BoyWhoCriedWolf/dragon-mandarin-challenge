import os
import re

from django.shortcuts import get_object_or_404
from mainapp.reading.utils import clean_article_body, strip_tags
from django.contrib import messages
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView
from mainapp.models import Article

def clean_sample_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Remove spaces between tags, which quill renders as blank paragraphs
    return re.sub(r">\s*<", "><", html).strip()


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'mainapp/articles/article_detail.jinja'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Article, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nopad'] = True
        context['noindex'] = True
        return context


class ArticleLoadingView(DetailView):
    model = Article
    template_name = 'mainapp/articles/article_loading.jinja'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return Article.objects.get(uuid=uuid)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_ready_to_view:
            # We've already processed this object, redirect to it immediately
            return HttpResponseRedirect(self.object.get_absolute_url())
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


