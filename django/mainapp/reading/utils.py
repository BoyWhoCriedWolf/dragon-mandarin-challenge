import re

import unicodedata
import xml

from bs4 import BeautifulSoup

from mainapp.models import Annotation, Word, CharacterPinyin
import lxml
import html

from lxml.html import fromstring
from lxml.html.clean import Cleaner



def print_aligned(s, annotation):
    def get_str_display_width(unicode_str):
        # east_asian_width returns 'F' or 'W' for characters that are double width
        return len(unicode_str) + sum(unicodedata.east_asian_width(c) in 'FW' for c in unicode_str)

    i, length, cp_or_word = annotation
    if type(cp_or_word) in [CharacterPinyin, Word]:
        char_string = cp_or_word.char_string
    else:
        char_string = cp_or_word
    print(s)
    print(' ' * get_str_display_width(s[:i]) + '^' * get_str_display_width(s[i:i+length]))
    if char_string:
        print(' ' * get_str_display_width(s[:i]) + char_string)


def show_annotations(article):
    print("WORD ANNOTATIONS:")
    for annotation in Annotation.objects.filter(
        article=article,
        type__in=[Annotation.TYPE_WORD, Annotation.TYPE_CHARACTER],
    ):
        print()
        print_aligned(article.body, (annotation.start, annotation.length, annotation.word or annotation.cp))

    print("\nPHRASE ANNOTATIONS:")
    for annotation in Annotation.objects.filter(article=article, type=Annotation.TYPE_PHRASE):
        print()
        print(article.body[annotation.start:annotation.start+annotation.length])
        print(annotation.phrase.english)



def strip_tags(s):
    tree = lxml.html.fromstring(s)
    return tree.text_content()


def clean_article_body(html_string):

    for old, new in [
        (['&amp;', '&#38;', '&#x26;'], '＆'),
        (['&lt;', '&#60;', '&#x3C;'], '＜'),
        (['&gt;', '&#62;', '&#x3E;'], '＞'),
        (['&quot;', '&#34;', '&#x22;'], '＂'),
        (['&apos;', '&#39;', '&#x27;'], '＇'),
    ]:
        for s in old:
            html_string = html_string.replace(s, new)
    html_string = html.unescape(html_string)

    allowed_tags = ['h2', 'p', 'ul', 'ol', 'li', 'strong', 'em']
    cleaner = Cleaner(allow_tags=allowed_tags, safe_attrs_only=True)
    document = lxml.html.fromstring(html_string)
    document = cleaner.clean_html(document)
    xml_string = lxml.etree.tostring(document, method="xml", encoding="UTF-8").decode("UTF-8")

    parser = lxml.etree.XMLParser(remove_blank_text=True)
    tree = lxml.etree.fromstring(xml_string, parser=parser)
    xml_string = lxml.etree.tostring(tree, encoding="UTF-8").decode("UTF-8")

    for old, new in [
        (['\n'], ''),
    ]:
        for s in old:
            xml_string = xml_string.replace(s, new)

    return xml_string



def get_text(xml_fragment):
    if xml_fragment[:2] == '</':
        xml_fragment = '<' + xml_fragment[2:]

    soup = BeautifulSoup(xml_fragment, 'lxml')
    return soup.get_text()


def iter_text(xml_string):
    assert html.unescape(xml_string) == xml_string, "Check there are no HTML entities (like &amp;) in article body - this isn't supported"

    res = []

    def start_element(name, attrs):
        pass

    def end_element(name):
        pass

    def char_data(data):
        char_index = len(xml_string.encode('UTF-8')[:p.CurrentByteIndex].decode())
        res.append((char_index, data))


    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.Parse(xml_string, True)

    return res
























