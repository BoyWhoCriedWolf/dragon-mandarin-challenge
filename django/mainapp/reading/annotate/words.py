import re
import traceback

from asgiref.sync import async_to_sync, sync_to_async
from django.db import transaction, IntegrityError

from mainapp.models import Annotation, Word, CharacterPinyin, Meaning, Definition, Character, Pinyin, Syllable
from mainapp.reading.utils import iter_text
from mainapp.utils import HANZI_PATTERN

import jieba
jieba.initialize()

def _should_annotate(char_string):
    return bool(re.fullmatch(rf'[{HANZI_PATTERN}]+', char_string))

def _split_words(s):
    if not s:
        return []
    words = list(jieba.cut(s))
    assert ''.join(words) == s
    return words

def _get_individual_cps(word):
    cps = []
    for c in word:
        cp = CharacterPinyin.objects.filter(character__char=c).first()
        if cp:
            cps.append(cp)
        else:
            print(f"UserWarning: No CP exists with any pinyin for character {c} (appears inside word {word})")
            cps.append(None)

    return cps

def _get_or_create_db_object(word_str, word_data):
    if word_data:
        assert word_data['word'] == word_str
        word, pinyin, definition = word_data['word'], word_data['pinyin'], word_data['definition']
    else:
        word, pinyin, definition = word_str, None, None

    if not _should_annotate(word):
        return None

    if len(word) == 1:
        if not pinyin:
            cp = CharacterPinyin.objects.filter(character__char=word).first()
            if cp:
                return cp
            else:
                print(f"UserWarning: No CP exists with any pinyin for character {word['word']}")
                return None

        try:
            cp = CharacterPinyin.objects.get(character__char=word, pinyin__written=pinyin)
            with transaction.atomic():
                meaning = Meaning.objects.select_for_update().get(pk=cp.meaning.pk)
                meaning.definition_set.all().delete()
                Definition.objects.create(
                    meaning=meaning,
                    text=definition,
                    order=0,
                )
                cp.client_obj = cp.compute_client_obj()
                cp.save()
            return cp

        except CharacterPinyin.DoesNotExist:
            print(f"UserWarning: Creating new unverified CP: {word}/{pinyin}")
            try:
                cp, created = CharacterPinyin.objects.get_or_create(
                    character=Character.objects.get(char=word),
                    pinyin=Pinyin.objects.get_from_str(pinyin),
                )
                if created:
                    cp.client_obj = cp.compute_client_obj()
                    cp.save()
            except (Syllable.DoesNotExist, Pinyin.DoesNotExist):
                print(f"UserWarning: Unknown pinyin: {pinyin} - check the characters carefully, this may be because GPT gave a weird character that looks the same but is wrong")
                cp = None

            return cp

    else:
        if not pinyin:
            obj = Word.objects.filter(char_string=word).first()
            if obj:
                return obj
            else:
                print(f"UserWarning: No Word exists with any pinyin for character {word}, falling back to individual characters")
                return _get_individual_cps(word)

        try:
            obj = Word.objects.get(char_string=word, pinyin_string=pinyin)
            with transaction.atomic():
                meaning = Meaning.objects.select_for_update().get(pk=obj.meaning.pk)
                meaning.definition_set.all().delete()
                Definition.objects.create(
                    meaning=meaning,
                    text=definition,
                    order=0,
                )
                obj.client_obj = obj.compute_client_obj()
                obj.save()
            return obj

        except Word.DoesNotExist:
            print(f"UserWarning: Creating new unverified word: {word}/{pinyin}")
            try:
                obj = Word.create_from_chars(
                    char_string=word,
                    pinyin_list=pinyin.split(' '),
                    definition=definition,
                )
            except (Pinyin.DoesNotExist, Syllable.DoesNotExist):
                print(f"UserWarning: Unknown pinyin: {pinyin} - check the characters carefully, this may be because GPT gave a weird character that looks the same but is wrong")
                obj = None

            except IntegrityError:
                # Probably a race condition where the Word was already created by another process
                obj = Word.objects.get(char_string=word, pinyin_string=word)

            return obj


def _get_db_object(word):
    if not _should_annotate(word):
        return None

    if len(word) == 1:
        n_cps = len(Character.objects.get(char=word).get_common_pinyins())
        if n_cps == 1:
            cp = CharacterPinyin.objects.filter(
                character__char=word,
            ).first()
            return cp
        else:
            return None

    elif len(word) > 1:
        db_words = Word.objects.filter(char_string=word)
        n_words = len(db_words)
        if n_words == 1:
            return db_words.first()
        else:
            return None


async def _enrich_words(words, s, use_gpt=True):
    assert ''.join(words) == s, (words, s)

    word_objs = [
        {'word': word, 'obj': await sync_to_async(_get_db_object)(word) if _should_annotate(word) else None}
        for word in words
    ]

    unclear_words = []
    for x in word_objs:
        if _should_annotate(x['word']) and x['obj'] is None and x['word'] not in unclear_words:
            unclear_words.append(x['word'])

    unclear_words_enriched = {word: None for word in unclear_words}

    unclear_word_objs = {
        word: await sync_to_async(_get_or_create_db_object)(word, word_data)
        for word, word_data in unclear_words_enriched.items()
    }

    for x in word_objs:
        if x['obj'] is None and x['word'] in unclear_word_objs:
            x['obj'] = unclear_word_objs[x['word']]

    word_objs = [
        {
            'word': x['word'],
            'obj': await sync_to_async(_prefetch_fields)(x['obj'])
        }
        for x in word_objs
    ]

    assert ''.join([x['word'] for x in word_objs]) == s, (word_objs, s)
    return word_objs



def _prefetch_fields(obj):
    if not obj:
        return None
    if isinstance(obj, list):
        return [
            CharacterPinyin.objects.select_related('character', 'pinyin').get(pk=cp.pk)
            for cp in obj
        ]
    elif isinstance(obj, Word):
        return obj
    elif isinstance(obj, CharacterPinyin):
        return CharacterPinyin.objects.select_related('character', 'pinyin').get(pk=obj.pk)


async def _get_annotations_plain(s, use_gpt=True):
    try:
        words = _split_words(s)
        word_objs = await _enrich_words(words, s, use_gpt=use_gpt)
        word_objs = [
            {
                'word': x['word'],
                'obj': await sync_to_async(_prefetch_fields)(x['obj'])
            }
            for x in word_objs
        ]

    except Exception as e:
        traceback.print_exc()
        print("UserWarning: Unexpected error splitting/enriching words - this should be handled at the word level")
        return []

    assert ''.join([x['word'] for x in word_objs]) == s

    annotations = []
    i = 0
    for x in word_objs:
        if _should_annotate(x['word']) and x['obj']:
            if isinstance(x['obj'], list):
                assert len(x['word']) == len(x['obj'])
                for j, (c, obj) in enumerate(zip(x['word'], x['obj'])):
                    if obj:
                        annotations.append((i + j, 1, obj))
            else:
                annotations.append((i, len(x['word']), x['obj']))
        i += len(x['word'])

    return annotations

async def save_annotations_for_chunk(article, idx, length, use_gpt=True, cb=None):
    s = article.body[idx:idx + length]
    assert '<' not in s and '>' not in s, "This is supposed to be a single text node, it cannot contain any tags"
    annotations = [
        (x[0] + idx, x[1], x[2])
        for x in await _get_annotations_plain(s, use_gpt=use_gpt)
    ]
    for a_i, a_length, cp_or_word in annotations:
        assert article.body[a_i:a_i+a_length] == cp_or_word.char_string, (article.body[a_i:a_i+a_length], cp_or_word.char_string)


    print("starting save")
    annotations_for_saving = []
    new_cps, new_words = set(), set()  # Collect these for sending to the client
    for a_i, a_length, cp_or_word in annotations:
        annotation_type = {
            Word: Annotation.TYPE_WORD,
            CharacterPinyin: Annotation.TYPE_CHARACTER,
        }[type(cp_or_word)]
        annotations_for_saving.append(Annotation(
            article=article,
            field=Annotation.FIELD_BODY,
            type=annotation_type,
            start=a_i,
            length=a_length,
            word=cp_or_word if annotation_type == Annotation.TYPE_WORD else None,
            cp=cp_or_word if annotation_type == Annotation.TYPE_CHARACTER else None
        ))
        if isinstance(cp_or_word, CharacterPinyin):
            new_cps.add(cp_or_word)
        elif isinstance(cp_or_word, Word):
            new_words.add(cp_or_word)

    print(await Annotation.objects.filter(
        article=article,
        type__in=[Annotation.TYPE_WORD, Annotation.TYPE_CHARACTER],
        start__gte=idx,
        start__lt=idx + length,
    ).adelete())
    await Annotation.objects.abulk_create(annotations_for_saving)
    print(f"Saved {len(annotations_for_saving)} word/CP annotations")
    if cb:
        await cb(new_cps, new_words)



def fast_annotate(article):
    """
    Annotate all Words and CPs in the article using jieba with no GPT calls.
    """
    for i, text_chunk in iter_text(article.body):
        async_to_sync(save_annotations_for_chunk)(article, i, len(text_chunk), use_gpt=False)


