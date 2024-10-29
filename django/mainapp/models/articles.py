import string
import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse

from mainapp.models import Word, CharacterPinyin


def generate_uuid():
    length = 12
    chars = string.ascii_letters + string.digits
    while True:
        random_string = ''.join(secrets.choice(chars) for _ in range(length))
        if not Article.objects.filter(uuid=random_string).exists():
            break
    return random_string


class Article(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=12, unique=True, default=generate_uuid, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    english_title = models.CharField(max_length=200, null=True, blank=True)
    english_summary = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    is_ready_to_view = models.BooleanField(default=False, help_text="False until we've run all the celery jobs required to view this article (splitting characters etc)")

    # Cached
    inflated = models.TextField(null=True, blank=True, help_text="Inflated XML, including the Chinese title")
    plaintext = models.TextField(null=True, blank=True, help_text="Title and body, stripped of all HTML tags")

    class Meta:
        unique_together = ('user', 'title')

    def __str__(self):
        return f'{self.uuid}'

    def get_absolute_url(self):
        return reverse('article_detail', args=(self.uuid,))

    @property
    def channel_name(self):
        return f"article-{self.pk}"

    @property
    def loading_channel_name(self):
        return f"loading-article-{self.pk}"

    def get_field(self, field):
        if field == Annotation.FIELD_TITLE:
            return f"<h1>{self.title}</h1>" if self.title else None
        elif field == Annotation.FIELD_BODY:
            return self.body if self.body else None
        else:
            raise AssertionError(f"Unknown field: {field}")

    def get_words(self):
        return Word.objects.filter(
            annotation__article=self,
            annotation__type=Annotation.TYPE_WORD,
        ).distinct()

    def get_cps(self):

        article_cps = CharacterPinyin.objects.filter(
            annotation__article=self,
            annotation__type=Annotation.TYPE_CHARACTER,
        ).distinct()
        word_cps = CharacterPinyin.objects.filter(
            wordchar__word__annotation__article=self,
            wordchar__word__annotation__type=Annotation.TYPE_WORD,
        ).distinct()

        res = set(article_cps) | set(word_cps)

        return res

    def get_phrases(self):
        return PhraseAnnotation.objects.filter(
            annotation__article=self,
            annotation__type=Annotation.TYPE_PHRASE,
        ).distinct()


class PhraseAnnotation(models.Model):
    text = models.TextField(help_text="The plain text of this phrase, without any HTML")
    context = models.TextField(help_text="The plain text of this phrase, including some context on either side")
    english = models.TextField(help_text="English translation of this phrase")
    is_placeholder=models.BooleanField(help_text="True if english field contains placeholder text (before we call GPT)")

    def __str__(self):
        return f'{self.english}'


    def compute_client_obj(self):
        return {
            'pk': self.pk,
            'english': self.english,
        }


class Annotation(models.Model):
    TYPE_CHARACTER = 'CH'
    TYPE_WORD = 'WO'
    TYPE_PHRASE = 'PH'

    TYPE_CHOICES = [
        (TYPE_CHARACTER, 'Character'),
        (TYPE_WORD, 'Word'),
        (TYPE_PHRASE, 'Phrase'),
    ]

    FIELD_TITLE = 'TI'
    FIELD_BODY = 'BO'

    FIELD_CHOICES = [
        (FIELD_TITLE, 'Title'),
        (FIELD_BODY, 'Body'),
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    field = models.CharField(max_length=2, choices=FIELD_CHOICES, help_text="Whether this annotation pertains to title or body of article")
    type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    start = models.PositiveIntegerField()
    length = models.PositiveSmallIntegerField()

    word = models.ForeignKey(Word, on_delete=models.CASCADE, blank=True, null=True)
    cp = models.ForeignKey(CharacterPinyin, on_delete=models.CASCADE, blank=True, null=True)
    phrase = models.OneToOneField(PhraseAnnotation, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        indexes = [
            # Composite index to speed up the delete query in annotate.py:save_annotations_for_chunk
            models.Index(fields=['article', 'type', 'start'], name='article_type_start_idx'),
        ]


    @property
    def end(self):
        return self.start + self.length


