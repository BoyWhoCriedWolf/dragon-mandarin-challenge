import re
import asyncio
import traceback

from mainapp import gpt
from mainapp.models import Annotation
from mainapp.models.articles import PhraseAnnotation
from mainapp.reading.utils import iter_text, get_text
from mainapp.utils import HANZI_PATTERN

PHRASE_PLACEHOLDER_MSG = "Loading translation..."

PHRASE_MAX_LENGTH = 30
PHRASE_DELIMITERS = ["。？", "；：，", "、"] #, "「」（）"]

def _split_phrases(xml_string, i=0):

    xml_string = xml_string.strip(''.join(PHRASE_DELIMITERS))

    if not re.search(rf'[{HANZI_PATTERN}\d+]', xml_string):
        return None

    if i == len(PHRASE_DELIMITERS):
        return [xml_string]

    if i > 0 and len(get_text(xml_string)) <= PHRASE_MAX_LENGTH:
        return [xml_string]

    pattern = rf'[{re.escape(PHRASE_DELIMITERS[i])}]'

    if i == 0:
        split_patterns = [
            pattern,
            r'</?(?:p|div|li|ol|ul)>',
        ]
        pattern = '|'.join(f'(?:{p})' for p in split_patterns)

    if re.search(pattern, xml_string):
        phrases = []
        for xml_chunk in re.split(pattern, xml_string):
            if xml_chunk:
                # print(f"{'    ' * i}chunk: {xml_chunk}")
                chunk_phrases = _split_phrases(xml_chunk, i + 1)
                if chunk_phrases:
                    phrases += chunk_phrases
        return phrases
    else:
        return _split_phrases(xml_string, i + 1)


def _get_phrase_annotations(xml_string):

    phrase_chunks = _split_phrases(xml_string)

    annotations = []
    if phrase_chunks:
        i = 0
        for chunk in phrase_chunks:
            a_start = xml_string.find(chunk, i)
            a_length = len(chunk)
            a_text = get_text(chunk)
            if a_text:
                CONTEXT_SIZE = 30
                a_context = get_text(
                    xml_string[max(a_start - CONTEXT_SIZE, 0):a_start + a_length + CONTEXT_SIZE]
                )
                annotations.append((a_start, a_length, a_text, a_context))
            i = a_start + a_length

    return annotations


async def _get_phrase_translation(phrase_text, surrounding_text):

    assert phrase_text in surrounding_text, (phrase_text, surrounding_text)

    next_char = surrounding_text[min(surrounding_text.find(phrase_text) + len(phrase_text), len(surrounding_text) - 1)]
    INCLUDE_TRAILING_CHARS = "。，？"
    if next_char in INCLUDE_TRAILING_CHARS:
        phrase_text = f'{phrase_text}{next_char}'

    prompt = f"""
    You are a Chinese teacher. Please translate the following phrase into English:

    "{phrase_text}"

    This phrase appears in the following context:

    "...{surrounding_text}..."

    You can use this context to assist your translation, but do not include it in your translation. You must only translate the target phrase.

    Return your answer as JSON in this form:

    {{"translation": <your translation>}}
    """

    try:
        res = (await gpt.get_response_async(prompt=prompt, json_keys=['translation']))['translation']
    except Exception as e:
        traceback.print_exc()
        print("Error getting phrase translation with GPT")
        res = "Translation unavailable"

    return res



async def _update_phrase(phrase, cb):
    phrase.english = await _get_phrase_translation(phrase.text, phrase.context)
    phrase.is_placeholder = False
    await phrase.asave()
    if cb:
        await cb(phrase)



def annotate_phrases_with_placeholders(article):

    Annotation.objects.filter(article=article, type=Annotation.TYPE_PHRASE).delete()

    n_annotations = 0
    for field in [Annotation.FIELD_TITLE, Annotation.FIELD_BODY]:
        if article.get_field(field):
            for i, length, phrase_text, phrase_context in _get_phrase_annotations(article.get_field(field)):
                phrase = PhraseAnnotation(
                    text=phrase_text,
                    context=phrase_context,
                    english=PHRASE_PLACEHOLDER_MSG,
                    is_placeholder=True,
                )
                phrase.save()
                annotation = Annotation(
                    article=article,
                    field=field,
                    type=Annotation.TYPE_PHRASE,
                    start=i,
                    length=length,
                    phrase=phrase,
                )
                annotation.save()
                n_annotations += 1
    print(f"Saved {n_annotations} placeholder phrase annotations.")


async def update_phrase_annotations(article, cb):

    phrases = PhraseAnnotation.objects.filter(
        annotation__article=article,
        annotation__type=Annotation.TYPE_PHRASE,
        is_placeholder=True,
    ).select_related('annotation__article')

    phrase_tasks = []
    async for phrase in phrases:
        phrase_tasks.append(_update_phrase(phrase, cb))

    await asyncio.gather(*phrase_tasks, return_exceptions=True)

