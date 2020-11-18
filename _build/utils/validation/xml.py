import os
import re
from glob import glob
from xml.etree import ElementTree as ET
from html import unescape
from .common import print_header, check, warning, error


# Reading --------------------------------------------------------------------------------
def read_gum_xml_files(dir):
    xml_dicts = [
        _read_gum_xml_dict(filepath)
        for filepath in sorted(glob(os.path.join(dir, '*.xml')))
    ]

    common_dicts = [
        _xml_dict_to_common_dict(d) for d in xml_dicts
    ]
    return xml_dicts, common_dicts


def _read_gum_xml_dict(filepath):
    slug = filepath.split(os.sep)[-1][:-4]
    with open(filepath, "r") as f:
        text = f.read()
    parsed = ET.fromstring(text)

    return {
        "filepath": filepath,
        "slug": slug,
        "text": text,
        "attrs": parsed.attrib,
        "parsed": parsed
    }

def tt_to_ptb(token, tag):
    tag = {
        "VH" : "VB",
        "VHD": "VBD",
        "VHG": "VBG",
        "VHN": "VBN",
        "VHP": "VBP",
        "VHZ": "VBZ",
        "VV": "VB",
        "VVD": "VBD",
        "VVG": "VBG",
        "VVN": "VBN",
        "VVP": "VBP",
        "VVZ": "VBZ",
        "SENT": ".",
        "(": "-LRB-",
        ")": "-RRB-",
        "[": "-LSB-",
        "]": "-RSB-",
        "PP": "PRP",
        "PP$": "PRP$",
        "IN/that": "IN",
        "NPS": "NNPS",
        "NP": "NNP",
    }.get(tag, tag)
    if token == '[':
        tag = '-LSB-'
    elif token == ']':
        tag = '-RSB-'
    return tag


def _xml_dict_to_common_dict(xml_dict):
    """
    Return a common dict given an xml dict, which contains the keys
    "tokens", "xpos", and "lemmas", each containing a list of sentences,
    which is in turn a list of the relevant unit
    """
    sentences = []

    sentence = []
    for line in xml_dict['text'].strip().split('\n'):
        line = line.strip()
        if line.startswith('<') and line.endswith('>'):
            if line == '</s>':
                sentences.append(list(map(unescape, sentence)))
                sentence = []
        else:
            sentence.append(line)

    tokens = [[t.split('\t')[0] for t in sentence]
              for sentence in sentences]
    xpos = [[tt_to_ptb(*t.split('\t')[:2]) for t in sentence]
            for sentence in sentences]
    lemmas = [[t.split('\t')[2] for t in sentence]
              for sentence in sentences]

    return {
        "slug": xml_dict['slug'],
        "tokens": tokens,
        "xpos": xpos,
        "lemmas": lemmas
    }


# Checking --------------------------------------------------------------------------------
def check_xml(args, xml_dicts):
    print_header("Validating XML files")

    check_filename_and_id_identical(xml_dicts)


@check("XML id attribute should equal filename minus extension")
def check_filename_and_id_identical(xml_dicts):
    for d in xml_dicts:
        if d['slug'] != d['attrs']['id']:
            error(d['slug'], f"has slug (from filename) {d['slug']}, but id attribute is {d['attrs']['id']}")






