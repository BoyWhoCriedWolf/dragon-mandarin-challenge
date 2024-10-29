
from mainapp.exceptions import InvalidPinyinException

import logging
logger = logging.getLogger('cndict')

MARKS = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
}

RARE_MARKS = {
    'r': ['*', 'ŕ', 'ř', '*'],
    'n': ['*', 'ń', 'ň', 'ǹ'],
    'm': ['%', 'ḿ', '*', '$'],
    'h': ['*', '*', 'ȟ', '*'],
}

ALL_MARKS = {**MARKS, **RARE_MARKS}

COMPOSITE_CHARS = {
    'm̀': '$',
    'm̄': '%',
}

EXTRA_MARK_LOCS = {
    'r': 0,
    'n': 0,
    'ng': 0,
    'm': 0,
    'h': 0,
    'hm': 0,
    'hng': 0,
}

def add_tone_mark(s, tone):
    if tone == 5:
        return s
    assert tone in [1, 2, 3, 4]

    for vowel in 'aoe':
        vowel_loc = s.find(vowel)
        if vowel_loc > -1:
            break
    else:
        vowel_loc = max(s.rfind(v) for v in 'iuü')
        if vowel_loc == -1:
            if s not in EXTRA_MARK_LOCS.keys():
                raise InvalidPinyinException(s)
            vowel_loc = EXTRA_MARK_LOCS[s]

    new_vowel = ALL_MARKS[s[vowel_loc]][tone - 1]
    if new_vowel == '*':
        raise InvalidPinyinException(s)
    res = list(s)
    res[vowel_loc] = new_vowel
    new_s = ''.join(res)
    for (k, v) in COMPOSITE_CHARS.items():
        new_s = new_s.replace(v, k)
    return new_s


def parse_pinyin(pinyin):
    if pinyin[-1].isdigit():
        if not pinyin[:-1].isalpha():
            raise InvalidPinyinException(pinyin)
        tone = int(pinyin[-1])
        if tone == 0:
            tone = 5
        return pinyin[:-1], tone

    pinyin = pinyin.replace('ê̄', 'ēi')
    pinyin = pinyin.replace('ế', 'éi')
    pinyin = pinyin.replace('ê̌', 'ěi')
    pinyin = pinyin.replace('ề', 'èi')

    for (k, v) in COMPOSITE_CHARS.items():
        pinyin = pinyin.replace(k, v)

    res = []
    tone = 5
    for c in pinyin:
        for (no_mark, marks_list) in ALL_MARKS.items():
            if c in marks_list:
                tone = marks_list.index(c) + 1
                res.append(no_mark)
                break
        else:
            if not c.isalpha():
                raise InvalidPinyinException(pinyin)
            res.append(c)
    return ''.join(res), tone


def normalise_pinyin(pinyin):
    pinyin = pinyin.lower()
    return add_tone_mark(*parse_pinyin(pinyin))


def remove_tone_marks(s):
    for k, v in ALL_MARKS.items():
        for mark in v:
            s = s.replace(mark, k)
    return s


def is_valid_pinyin(pinyin):
    try:
        parse_pinyin(pinyin)
        return True
    except InvalidPinyinException:
        return False

