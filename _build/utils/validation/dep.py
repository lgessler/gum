import os
import re
from collections import defaultdict
from glob import glob
import conllu
from .common import print_header, check, warning, error


# Reading --------------------------------------------------------------------------------
def read_gum_dep_files(dir):
    dep_dicts = [
        _read_gum_dep_dict(filepath)
        for filepath in sorted(glob(os.path.join(dir, '*.conllu')))
    ]

    common_dicts = [
        _dep_dict_to_common_dict(d) for d in dep_dicts
    ]
    return dep_dicts, common_dicts


def _read_gum_dep_dict(filepath):
    slug = filepath.split(os.sep)[-1][:-7]
    with open(filepath, "r") as f:
        text = f.read()
    parsed = conllu.parse(text)

    return {
        "filepath": filepath,
        "slug": slug,
        "text": text,
        "parsed": parsed
    }


def _dep_dict_to_common_dict(dep_dict):
    """
    Return a common dict given an dep dict, which contains the keys
    "tokens", "xpos", and "lemmas", each containing a list of sentences,
    which is in turn a list of the relevant unit
    """
    sentences = dep_dict['parsed']

    tokens = [[t['form'] for t in sentence]
              for sentence in sentences]
    xpos = [[t['xpos'] for t in sentence]
            for sentence in sentences]
    lemmas = [[t['lemma'] for t in sentence]
              for sentence in sentences]

    return {
        "slug": dep_dict['slug'],
        "tokens": tokens,
        "xpos": xpos,
        "lemmas": lemmas
    }


# Checking --------------------------------------------------------------------------------
def check_dep(args, dep_dicts):
    print_header("Validating dep files")

    check_filename_and_id_identical(dep_dicts)
    check_contiguous(dep_dicts)
    check_left_to_right(dep_dicts)
    check_no_chains(dep_dicts)
    if args.unreliable_checks:
        check_should_be_fixed(dep_dicts)
    check_should_not_be_fixed(dep_dicts)


def print_sentence(sentence, keys=('id', 'form', 'head', 'deprel'), highlight=()):
    min_i = max(min(highlight) - 2, 0)
    max_i = min(max(highlight) + 1, len(sentence))
    for t in sentence[min_i:max_i]:
        print(' ' if t['id'] not in highlight else '›️',
              '\t'.join(map(str, map(lambda x: t[x], keys))))


@check("Metadata item `newdoc id` should equal filename minus extension")
def check_filename_and_id_identical(dep_dicts):
    for d in dep_dicts:
        newdoc_id = d['parsed'][0].metadata['newdoc id']
        if not newdoc_id == d['slug']:
            error(d['slug'], f"has slug (from filename) {d['slug']}, but id attribute is {d['attrs']['id']}")


@check("`flat`, `goeswith` spans should be contiguous (except for PUNCT intervening)")
def check_contiguous(dep_dicts):
    for d in dep_dicts:
        for deprel in ['flat', 'goeswith']:
            for sentence in d['parsed']:
                sent_id = sentence.metadata['sent_id'].split('-')[-1]

                last_suitable_head = 0
                for t in sentence:
                    if t['deprel'] == deprel:
                        if t['head'] != last_suitable_head:
                            error(d['slug'], f'token {sent_id}-{t["id"]}: {deprel} tokens should be contiguous')
                            print_sentence(sentence, highlight=[t['id'], t['head'], last_suitable_head])

                    elif t['upos'] != 'PUNCT':
                        last_suitable_head = t['id']


@check("`flat`, `goeswith`, and `fixed` should go left-to-right")
def check_left_to_right(dep_dicts):
    for d in dep_dicts:
        for sentence in d['parsed']:
            sent_id = sentence.metadata['sent_id'].split('-')[-1]

            for t in sentence:
                deprel = t['deprel']
                if t['deprel'] in ['flat', 'goeswith', 'fixed']:
                    if t['head'] > t['id']:
                        error(d['slug'], f'token {sent_id}-{t["id"]}: {deprel} tokens must go from left to right')
                        print_sentence(sentence, highlight=[t['id'], t['head']])


@check("`flat`, `goeswith`, and `fixed` should always form fountains, not chains")
def check_no_chains(dep_dicts):
    for d in dep_dicts:
        for sentence in d['parsed']:
            sent_id = sentence.metadata['sent_id'].split('-')[-1]

            for t in sentence:
                deprel = t['deprel']
                head = t['head']
                if head == 0 or deprel not in ["flat", "goeswith", "fixed"]:
                    continue

                if sentence[head-1]['deprel'] == deprel:
                    error(d['slug'], f"f'token {sent_id}-{t['id']}: {deprel} chain should be a fountain")
                    print_sentence(sentence, highlight=[t['id'], head, sentence[head]['head']])

# See: http://corpling.uis.georgetown.edu/wiki/doku.php?id=gum:dependencies#using_fixed_and_goeswith
# Divided into FIXED_ALWAYS and FIXED_SOMETIMES depending on whether we can be 99% certain
# about fixed status just from the strings
FIXED_ALWAYS = [
    ["according", "to"],
    ["all", "but"],
    ["all", "in", "all"],
    ["as", "if"],
    # ["as", "in"],
    ["as", "of"],
    ["as", "opposed", "to"],
    ["as", "such"],
    ["as", "to"],
    ["as", "well"],
    # ["as", "well", "as"],
    # ["at", "least"],
    ["because", "of"],
    # ["depending", "on"],
    # ["depending", "upon"],
    ["due", "to"],
    ["had", "better"], ["'d", "better"],
    ["how", "come"],
    ["instead", "of"],
    ["in", "between"],
    ["in", "case"],
    ["in", "case", "of"],
    ["in", "order"],
    # ["kind", "of"],
    # ["less", "than"],
    ["let", "alone"],
    # ["more", "than"],
    ["not", "to", "mention"],
    ["of", "course"],
    # ["out", "of"],
    ["per", "se"],
    ["prior", "to"],
    ["rather", "than"],
    ["so", "as", "to"],
    ["so", "that"],
    # ["sort", "of"],
    ["such", "as"],
    ["that", "is", ","], # added comma
    ["then", "again"],
    # ["up", "to"],
    ["vice", "versa"],
    ["whether", "or", "not"],
]

FIXED_SOMETIMES = [
    ["as", "in"],
    ["as", "well", "as"],
    ["at", "least"],
    ["depending", "on"],
    ["depending", "upon"],
    ["kind", "of"],
    ["less", "than"],
    ["more", "than"],
    ["out", "of"], # moved down because of particle verb cases
    ["sort", "of"],
    ["up", "to"],
]

FIXED_STRINGS = [" ".join(expr) for expr in FIXED_ALWAYS] + [" ".join(expr) for expr in FIXED_SOMETIMES]


@check("Items on the fixed list should be fixed (WARNING: some false positives)")
def check_should_be_fixed(dep_dicts):
    for d in dep_dicts:
        for sentence in d['parsed']:
            sent_id = sentence.metadata['sent_id'].split('-')[-1]

            for i in range(len(sentence)):
                remaining = sentence[i:]
                for fixed_item in FIXED_ALWAYS:
                    if (
                        all(pair[0]['form'].lower() == pair[1].lower() for pair in zip(remaining, fixed_item))
                        and not all(t['deprel'] == 'fixed' for t in sentence[i+1:i+len(fixed_item)])
                    ):
                        error(d['slug'], f"f'token {sent_id}-{i+1}: \"{' '.join(fixed_item)}\" should be a fixed expression")
                        print_sentence(sentence, highlight=range(i+1, i+1+len(fixed_item)))


@check("Items not on the fixed list should not be fixed")
def check_should_not_be_fixed(dep_dicts):
    for d in dep_dicts:
        for sentence in d['parsed']:
            sent_id = sentence.metadata['sent_id'].split('-')[-1]

            fixeds = defaultdict(list)
            for t in sentence:
                if t['deprel'] == 'fixed':
                    fixeds[t['head']].append(t['id'])

            for head_id, child_ids in fixeds.items():
                get_token = lambda id_: sentence[id_-1]['form'].lower()
                expr = " ".join([get_token(head_id)] + list(map(get_token, child_ids)))
                if expr not in FIXED_STRINGS:
                    error(d['slug'], f"token {sent_id}-{head_id}: \"{expr}\" is not a valid fixed")
                    print_sentence(sentence, highlight=[head_id] + child_ids)


