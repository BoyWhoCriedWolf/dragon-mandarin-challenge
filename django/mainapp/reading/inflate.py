import itertools
import uuid
from collections import defaultdict

from mainapp.models import Annotation, Word, CharacterPinyin, update_atomic
from mainapp.reading.utils import iter_text

import xxhash

def _fasthash(str):
    return xxhash.xxh32(str).hexdigest()[-6:]

def inflate_text(text, annotations, char_phrases, chunk_offset):
    assert len(char_phrases) == len(text)

    chars = []
    j = 0
    for i, c in enumerate(text):
        if j == len(annotations):
            char_obj = None
            group_key = uuid.uuid4().hex
        else:
            if i >= annotations[j][0] + annotations[j][1]:
                j += 1

            if j < len(annotations) and annotations[j][0] <= i:
                char_obj = annotations[j][2]
                group_key = j
            else:
                char_obj = None
                group_key = uuid.uuid4().hex

        if c == ' ':
            c = '&nbsp;'

        chars.append({
            'char': c,
            'obj': char_obj,
            'group_key': group_key,
            'phrase': char_phrases[i],
        })

        counters = defaultdict(int)  # maps char_string -> current char_string_counter
        group_keys_seen = set()
        for char in chars:
            if char['obj'] is None:
                char_string = c
            else:
                char_string = char['obj'].char_string
            if char['group_key'] not in group_keys_seen:
                counters[char_string] += 1
            char['cid'] = f"{chunk_offset}-{_fasthash(char_string)}-{counters[char_string]}"
            group_keys_seen.add(char['group_key'])


    def char_key(char):
        return char['group_key']


    def render_group(g, i):
        g = list(g)
        if len(g) > 1 or isinstance(g[0]['obj'], Word):
            assert all(char['obj'] == g[0]['obj'] for char in g)
            assert all(char['cid'] == g[0]['cid'] for char in g)

            assert all(char['phrase'] == g[0]['phrase'] for char in g), f"Check that phrase annotations do not split Word annotations: {g}"

            char_string = "".join([char["char"] for char in g])
            return f'<d:word cid="{g[0]["cid"]}" obj="{g[0]["obj"].pk}" phrase="{g[0]["phrase"].pk if g[0]["phrase"] else ""}">{char_string}</d:word>'

        else:
            assert len(g) == 1
            char = g[0]
            if isinstance(char['obj'], CharacterPinyin):
                return f'<d:cp cid="{char["cid"]}" obj="{char["obj"].pk}" phrase="{char["phrase"].pk if char["phrase"] else ""}">{char["char"]}</d:cp>'

            elif char['obj'] is None:
                return f'<d:plain cid="{char["cid"]}" phrase="{char["phrase"].pk if char["phrase"] else ""}">{char["char"]}</d:plain>'


    res = ''
    for i, (k, g) in enumerate(itertools.groupby(chars, char_key)):
        res += render_group(g, i)

    return res


def inflate_xml(article, field):

    if not article.get_field(field):
        return ''

    annotations = list(Annotation.objects.filter(
        article=article,
        field=field,
        type__in=[Annotation.TYPE_CHARACTER, Annotation.TYPE_WORD],
    ).order_by('start'))
    phrase_annotations = list(Annotation.objects.filter(
        article=article,
        field=field,
        type=Annotation.TYPE_PHRASE,
    ).order_by('start'))

    replacements = []
    j = 0
    k = 0
    for i, text in iter_text(article.get_field(field)):

        if j == len(annotations):
            chunk_annotations = []
            char_phrases = [None] * len(text)
        else:
            chunk_annotations = []
            if annotations:
                while True:
                    assert annotations[j].start >= i
                    if annotations[j].end <= i + len(text):
                        chunk_annotations.append(
                            (annotations[j].start - i, annotations[j].length, annotations[j].word or annotations[j].cp)
                        )
                        j += 1
                        if j == len(annotations):
                            break
                    else:
                        break

            char_phrases = []
            for c in range(len(text)):
                if k < len(phrase_annotations) and i + c >= phrase_annotations[k].end:
                    k += 1
                if k == len(phrase_annotations):
                    char_phrase = None
                else:
                    assert i + c < phrase_annotations[k].end
                    if i + c >= phrase_annotations[k].start:
                        char_phrase = phrase_annotations[k].phrase
                    else:
                        char_phrase = None
                char_phrases.append(char_phrase)

        replacements.append((i, i+len(text), inflate_text(text, chunk_annotations, char_phrases, i)))

    new_body = list(article.get_field(field))
    for start, end, replace_with in reversed(replacements):
        new_body[start:end] = replace_with

    return ''.join(new_body)

def save_inflated(article):
    inflated = inflate_xml(article, Annotation.FIELD_TITLE) + inflate_xml(article, Annotation.FIELD_BODY)
    update_atomic(article, 'inflated', inflated)
























