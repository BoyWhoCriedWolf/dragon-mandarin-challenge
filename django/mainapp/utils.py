import itertools
import logging
import os
import re
import sys

HANZI_PATTERN = r'\u4e00-\u9fff'
PINYIN_NUMERIC_PATTERN = r'A-Za-z12345'

logger = logging.getLogger('cndict')

def is_hanzi(char_string):
    pattern = r'^[%s]+$' % HANZI_PATTERN
    return bool(re.match(pattern, char_string))

def get_number(s):
    if not s:
        return s
    remove_chars = ",，年%"
    for char in remove_chars:
        s = s.replace(char, '')
    if s.isdigit():
        return int(s)
    return None

def init_log(filename=None):
    """
    Log INFO and above to stdout, DEBUG and above to file if supplied.
    """
    logger = logging.getLogger('cndict')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)15s:%(lineno)-4d: %(message)s')

    if filename:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)


def make_full_url(url):
    assert not url.startswith('http')
    return f'https://dragonmandarin.com{url}'


# https://stackoverflow.com/a/17870684
def find_sublist(l, sl):
    # Returns the first index of sublist sl inside list l, -1 if not found (like string.find(substring) but for lists)
    sll=len(sl)
    for ind in (i for i,e in enumerate(l) if e==sl[0]):
        if l[ind:ind+sll]==sl:
            return ind
    return -1


