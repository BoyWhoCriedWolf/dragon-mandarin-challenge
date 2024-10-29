import re

from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.db import models
from django.db.models import Min, Q

from mainapp.pinyin import add_tone_mark, parse_pinyin, normalise_pinyin, is_valid_pinyin

from mainapp.utils import HANZI_PATTERN


class CharacterPinyin(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE)
    pinyin = models.ForeignKey('Pinyin', on_delete=models.CASCADE)
    is_cn_variant = models.BooleanField(null=True, blank=True, help_text="Null unless this pinyin is specific to either Mainland (True) or Taiwan (False)")
    meaning = models.ForeignKey('Meaning', null=True, blank=True, on_delete=models.SET_NULL, help_text="for single-character words")

    # Cached
    client_obj = JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('character', 'pinyin',)

    def __str__(self):
        return f'{self.character.char} {self.pinyin.written}'

    @property
    def char_string(self):
        return self.character.char

    def compute_client_obj(self):
        return {
            'pk': self.pk,
            'isVerified': True,
            'type': 'cp',
            'url': '#',
            'chinese': self.character.char,
            'pinyin': self.pinyin.written,
            'tone': self.pinyin.tone,
            'definitions': [x.text for x in self.meaning.definition_set.order_by('order')] if self.meaning else [],
            'hskLevel': None,
            'freqRank': None,
        }


class CharacterVariant(models.Model):
    SIMPLIFIED = 'CN'
    TRADITIONAL = 'TW'
    VARIANT_TYPE_CHOICES = (
        (SIMPLIFIED, 'Simplified variant'),
        (TRADITIONAL, 'Traditional variant'),
    )
    base = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='base_reverse')
    variant = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='variant_reverse')
    variant_type = models.CharField(max_length=2, choices=VARIANT_TYPE_CHOICES)


class Character(models.Model):
    char = models.CharField(null=True, blank=True, max_length=1, unique=True)
    pinyins = models.ManyToManyField('Pinyin', through='CharacterPinyin')

    def __str__(self):
        return self.char

    def get_common_pinyins(self, thresh=0.05):
        return CharacterPinyin.objects.filter(
            character=self,
        ).values_list('pinyin__written', flat=True)

    def compute_client_obj(self):
        cp = CharacterPinyin.objects.filter(character=self).first()
        return {
            'pk': self.pk,
            'type': 'char',
            'url': '#',
            'chinese': self.char,
            'tone': cp.pinyin.tone if cp else 5,
            'pinyin': cp.pinyin.written if cp else '',
            'definitions': [],
            'hskLevel': None,
            'freqRank': None,
        }

    def get_simplified_variants(self):
        return Character.objects.filter(
            pk__in=CharacterVariant.objects.filter(
                base=self,
                variant_type=CharacterVariant.SIMPLIFIED,
            ).values_list('variant__pk', flat=True)
        )

    def get_traditional_variants(self):
        return Character.objects.filter(
            pk__in=CharacterVariant.objects.filter(
                base=self,
                variant_type=CharacterVariant.TRADITIONAL,
            ).values_list('variant__pk', flat=True)
        )


class Syllable(models.Model):
    initial = models.CharField(null=True, blank=True, max_length=2)
    final = models.CharField(null=True, blank=True, max_length=4)
    written = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.written


class PinyinManager(models.Manager):
    def get_from_str(self, pinyin_str, create=False):
        s, tone = parse_pinyin(pinyin_str)
        if create:
            syllable, created = Syllable.objects.get_or_create(written=s)
            if created:
                print(f"Created syllable: {s}")
            pinyin, created = Pinyin.objects.get_or_create(syllable=syllable, tone=tone, written=add_tone_mark(s, tone))
            if created:
                print(f"Created pinyin: {s, tone}")
        else:
            syllable = Syllable.objects.get(written=s)
            pinyin = Pinyin.objects.get(syllable=syllable, tone=tone)
        return pinyin


class Pinyin(models.Model):
    syllable = models.ForeignKey('Syllable', on_delete=models.CASCADE)
    tone = models.PositiveSmallIntegerField(help_text="1 to 5 inclusive")

    # Cached
    written = models.CharField(max_length=6, unique=True, help_text="Written pinyin including tone mark")
    written_numeric = models.CharField(max_length=7, null=True, blank=True, help_text="Written pinyin with number instead of diacritic (e.g. hao3)")

    objects = PinyinManager()

    class Meta:
        unique_together = ('syllable', 'tone',)

    def __str__(self):
        return self.written

    def get_written_numeric(self):
        return f'{self.syllable.written}{self.tone}'


class Word(models.Model):

    CN = 'CN'
    TW = 'TW'
    NUMBER = 'NU'
    TAG_CHOICES = (
        (CN, 'Known to be used in Mainland'),
        (TW, 'Known to be used in Taiwan'),
        (NUMBER, 'This word is a number'),
    )
    characters = models.ManyToManyField('CharacterPinyin', through='WordChar')
    meaning = models.ForeignKey('Meaning', on_delete=models.CASCADE)
    tags = ArrayField(models.CharField(max_length=2, choices=TAG_CHOICES), default=list)

    # Cached
    char_string = models.CharField(max_length=20, db_index=True)
    pinyin_string = models.CharField(max_length=200, db_index=True)
    pinyin_string_numeric = models.CharField(max_length=200)
    pinyin_slug = models.CharField(null=True, blank=True, max_length=100, db_index=True)
    client_obj = JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['char_string', 'pinyin_string'], name='unique_char_pinyin'),
        ]

    @classmethod
    def create_from_chars(cls, char_string, pinyin_list, definition=None, tags=None):
        assert len(char_string) == len(pinyin_list), (char_string, pinyin_list)
        # Make sure there's no punctuation or weird stuff
        assert re.match(rf'^[{HANZI_PATTERN}]+$', char_string), char_string
        assert all((is_valid_pinyin(x) for x in pinyin_list)), pinyin_list

        meaning = Meaning()
        meaning.save()
        if definition:
            Definition.objects.create(
                meaning=meaning,
                text=definition,
                order=0,
            )

        word = Word(
            meaning=meaning,
            char_string=char_string,
            pinyin_string=' '.join(normalise_pinyin(x) for x in pinyin_list),
        )
        word.save()

        if tags:
            for tag in tags:
                if tag and tag not in word.tags:
                    word.tags.append(tag)
            word.save()

        # Fill the new Word object with WordChar
        for i, (char, pinyin_str) in enumerate(zip(char_string, pinyin_list)):
            character = Character.objects.get(char=char)
            pinyin = Pinyin.objects.get_from_str(pinyin_str)
            # Allow CP creation
            cp, created = CharacterPinyin.objects.get_or_create(
                character=character,
                pinyin=pinyin,
            )
            if created:
                cp.sources.append('article')
                cp.client_obj = cp.compute_client_obj()
                cp.save()

            WordChar(
                word=word,
                character_pinyin=cp,
                order=i,
            ).save()
        assert word.char_string == word.compute_char_string()
        assert word.pinyin_string == word.compute_pinyin_string()

        word.pinyin_slug = word.compute_pinyin_slug()
        word.client_obj = word.compute_client_obj()  # Requires word.pinyin_slug
        word.pinyin_string_numeric = word.compute_pinyin_string_numeric()
        word.save()
        return word

    def __str__(self):
        return f"{self.char_string} {self.pinyin_string}"

    def compute_char_string(self):
        return ''.join([
            x.character_pinyin.character.char if x.character_pinyin else x.punctuation
            for x in WordChar.objects.filter(word=self).order_by('order')
        ])

    def compute_pinyin_string(self):
        return ' '.join([
            x.character_pinyin.pinyin.written if x.character_pinyin else x.punctuation
            for x in WordChar.objects.filter(word=self).order_by('order')
        ])

    def compute_pinyin_string_numeric(self):
        return ' '.join(
            x.character_pinyin.pinyin.written_numeric if x.character_pinyin else x.punctuation
            for x in WordChar.objects.filter(word=self).order_by('order')
        )

    def compute_pinyin_slug(self):
        return '-'.join(
            x.character_pinyin.pinyin.written
            for x in WordChar.objects.filter(word=self).order_by('order') if x.character_pinyin
        )

    def compute_client_obj(self):
        return {
            'pk': self.pk,
            'isVerified': True,
            'type': 'word',
            'url': '#',
            'chinese': self.char_string,
            'tones': [
                # 5 is for punctuation etc because `tones` and `chinese` lists need to be the same length
                x.character_pinyin.pinyin.tone if x.character_pinyin else 5
                for x in WordChar.objects.filter(word=self).order_by('order')
            ],
            'pinyin': [
                x.character_pinyin.pinyin.written if x.character_pinyin else ''
                for x in WordChar.objects.filter(word=self).order_by('order')
            ],
            # cps contains pks of CPs in this word, but it's not sufficient to reconstruct the word since some words
            # contain punctuation, therefore the above (chinese, tones, pinyin) are still necessary. (cps is necessary
            # because we need to render component CPs in the sidebar under the word info).
            'cps': [wc.character_pinyin.pk for wc in self.wordchar_set.all().order_by('order') if wc.character_pinyin],
            'definitions': [x.text for x in self.meaning.definition_set.order_by('order')],
            'hskLevel': None,
            'freqRank': None,

        }

    def get_same_character_variants(self):
        return Word.objects.filter(
            char_string=self.char_string
        ).exclude(pk=self.pk)


class WordChar(models.Model):

    COMMA = '，'
    ENUM_COMMA = '、'
    MIDDOT = '・'
    PUNCTUATION_CHOICES = (
        (COMMA, COMMA),
        (ENUM_COMMA, ENUM_COMMA),
        (MIDDOT, MIDDOT),
    )
    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    # Exactly one of (character_pinyin, punctuation) must be set
    character_pinyin = models.ForeignKey('CharacterPinyin', null=True, blank=True, on_delete=models.CASCADE)
    punctuation = models.CharField(null=True, blank=True, max_length=1, choices=PUNCTUATION_CHOICES)
    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['word', 'order'], name='unique_order_word'),
            # Either character_pinyin or punctuation must be set, and not both
            models.CheckConstraint(
                check=(
                    (Q(character_pinyin__isnull=True) & Q(punctuation__isnull=False)) |
                    (Q(character_pinyin__isnull=False) & Q(punctuation__isnull=True))
                ),
                name=f'wordchar_character_or_punctuation',
            )
        ]
        ordering = ['order']


class Definition(models.Model):
    meaning = models.ForeignKey('Meaning', on_delete=models.CASCADE)
    text = models.TextField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['meaning', 'order'], name='unique_order_definition')
        ]
        ordering = ['order']

    def __str__(self):
        return self.text


class MeaningManager(models.Manager):

    def find_all(self, chars):
        return Meaning.objects.filter(word__char_string=chars)

    def get_unique(self, chars, pinyin):
        try:
            return Word.objects.get(char_string=chars, pinyin_string=pinyin).meaning
        except Word.DoesNotExist:
            return None


class Meaning(models.Model):

    objects = MeaningManager()

    def __str__(self):
        return '/'.join([x.char_string for x in self.word_set.all()])

    def get_hsk_level(self):
        return self.word_set.aggregate(Min('hsk_level'))['hsk_level__min']








