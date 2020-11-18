from collections import defaultdict

from .common import print_header, error, warning, check


def check_multilayer(args, common_dicts):
    """
    common_dicts should be a map keyed by one of {xml, tsv, dep, rst}.
    each key is paired with a dict that must contain keys {slug, tokens} and may contain {lemma, xpos}.
    The value paired with tokens, lemma, or xpos is a list of lists representing sentences and token-level info
    """
    print_header("Performing multilayer validations")

    if not check_documents(common_dicts):
        return
    combined_dicts = defaultdict(dict)
    for source, documents in common_dicts.items():
        for document in documents:
            combined_dicts[document['slug']][source] = document

    check_sentences(combined_dicts)
    check_tokens(combined_dicts)
    check_lemmas(combined_dicts)
    check_xpos(combined_dicts)


@check("All sources should have documents that are identically named")
def check_documents(common_dicts):
    sources = list(common_dicts.keys())
    attested = defaultdict(list)
    for source, documents in common_dicts.items():
        for document in documents:
            attested[document['slug']].append(source)

    errors = False
    for doc_name, attested_sources in attested.items():
        if len(attested_sources) != len(sources):
            errors = True
            error(f"{doc_name}", f"attested only in formats {', '.join(attested_sources)} "
                                 f"(should have {', '.join(sources)})")

    return errors


@check("Sentence counts should be identical")
def check_sentences(combined_dicts):
    for slug, dicts in combined_dicts.items():
        lens = [len(sentences) for sentences in dicts.values()]
        if not all(lens[0] == l for l in lens[1:]):
            error(slug, f"formats have different number of sentences: "
                        f"{ {source: len(sentences) for source, sentences in dicts.items()} }")


@check("Tokens should be identical")
def check_tokens(combined_dicts):
    for slug, dicts in combined_dicts.items():
        sources = list(dicts.keys())
        for i in range(len(dicts[sources[0]]['tokens'])):
            sentences = [dicts[source]['tokens'][i] for source in sources]
            s2lens = {source: len(dicts[source]['tokens'][i]) for source in sources}
            if not all(len(sentences[0]) == len(s) for s in sentences[1:]):
                error(slug, f"sentence {i} has varying lengths: {s2lens}")
            for j in range(min(s2lens.values())):
                tokens = [dicts[source]['tokens'][i][j] for source in sources]
                if not all(tokens[0] == token for token in tokens[1:]):
                    error(slug, f"sentence {i} has varying tokens at position {j}: "
                                f"{[(source, dicts[source]['tokens'][i][j]) for source in sources]}")

@check("Lemmas should be identical")
def check_lemmas(combined_dicts):
    for slug, dicts in combined_dicts.items():
        sources = [source for source in dicts.keys() if source in ['dep', 'xml']]
        for i in range(len(dicts[sources[0]]['lemmas'])):
            sentences = [dicts[source]['lemmas'][i] for source in sources]
            s2lens = {source: len(dicts[source]['lemmas'][i]) for source in sources}
            if not all(len(sentences[0]) == len(s) for s in sentences[1:]):
                error(slug, f"sentence {i} has varying lengths: {s2lens}")
            for j in range(min(s2lens.values())):
                lemmas = [dicts[source]['lemmas'][i][j] for source in sources]
                if not all(lemmas[0] == lemma for lemma in lemmas[1:]):
                    error(slug, f"sentence {i} has varying lemmas at position {j}: "
                                f"{[(source, dicts[source]['lemmas'][i][j]) for source in sources]}")


@check("XPOS tags should be identical")
def check_xpos(combined_dicts):
    for slug, dicts in combined_dicts.items():
        sources = [source for source in dicts.keys() if source in ['dep', 'xml']]
        for i in range(len(dicts[sources[0]]['xpos'])):
            sentences = [dicts[source]['xpos'][i] for source in sources]
            s2lens = {source: len(dicts[source]['xpos'][i]) for source in sources}
            if not all(len(sentences[0]) == len(s) for s in sentences[1:]):
                error(slug, f"sentence {i} has varying lengths: {s2lens}")
            for j in range(min(s2lens.values())):
                xpos = [dicts[source]['xpos'][i][j] for source in sources]
                if not all(xpos[0] == x for x in xpos[1:]):
                    error(slug, f"sentence {i} has varying xpos at position {j}: "
                                f"{[(source, dicts[source]['xpos'][i][j]) for source in sources]}")






