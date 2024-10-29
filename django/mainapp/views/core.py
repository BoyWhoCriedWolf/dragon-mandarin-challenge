import os
import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import ModelForm, CharField
from django.urls import reverse
from django.views.generic import CreateView

from mainapp import tasks
from mainapp.models import Article
from mainapp.reading import ARTICLE_LENGTH_LIMIT
from mainapp.reading.utils import strip_tags, clean_article_body

sample_dir = os.path.join(os.path.dirname(__file__), 'sample_articles')
with open(os.path.join(sample_dir, 'news.html'), 'r') as f:
    sample_news = f.read()
with open(os.path.join(sample_dir, 'blogpost.html'), 'r') as f:
    sample_blogpost = f.read()
with open(os.path.join(sample_dir, 'book.html'), 'r') as f:
    sample_book = f.read()

class IndexForm(ModelForm):

    url = CharField(required=False)

    class Meta:
        model = Article
        fields = ['body']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        body = cleaned_data.get('body')
        url = cleaned_data.get('url')

        if not body and not url:
            if not self.errors:
                raise ValidationError("Please provide either a URL or the article text below.")

        return cleaned_data

    def clean_body(self):
        if not self.cleaned_data['body']:
            return self.cleaned_data['body']

        submitted_len = len(strip_tags(self.cleaned_data['body']))
        if submitted_len > ARTICLE_LENGTH_LIMIT:
            raise ValidationError(f"Text too long: The reader is currently limited to 3000 characters per article (your submission was {submitted_len} characters).")

        body = clean_article_body(self.cleaned_data['body'])
        return body

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if not url.startswith('http'):
            url = f'https://{url}'
        if url and not self.data.get('body'):
            try:
                URLValidator()(url)
            except ValidationError:
                raise ValidationError("Please enter a valid URL.")
        return url

    def save(self, commit=True):
        article = super().save(commit=False)
        url = self.cleaned_data.get('url')
        if url and not self.data.get('body'):
            article.url = url

        if commit:
            article.save()
        return article


def clean_sample_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return re.sub(r">\s*<", "><", html).strip()


class IndexView(CreateView):
    model = Article
    template_name = 'mainapp/index.jinja'
    form_class = IndexForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['samples'] = [clean_sample_html(x) for x in [sample_news, sample_blogpost, sample_book]]
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        print("UserWarning: New request")
        self.object = form.save()
        tasks.process_article.delay_on_commit(self.object.pk)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('article_loading', args=(self.object.uuid, ))






