#!/usr/bin/env python
"""
Scan GUM's output .xml, .conllu, .tsv, and .rst for errors.
Errors are checked at the layer level and at the inter-layer level.

@author: Luke Gessler (lgessler)
@since: 2020-11-17
"""
import argparse
import os
from os.path import join as j
import utils.validation.xml as xml
import utils.validation.dep as dep
import utils.validation.multilayer as multilayer


def main(args):
    xml_dicts, xml_common_dicts = xml.read_gum_xml_files(args.xml_dir)
    xml.check_xml(args, xml_dicts)
    dep_dicts, dep_common_dicts = dep.read_gum_dep_files(args.dep_dir)
    dep.check_dep(args, dep_dicts)
    # TODO: tsv and rst
    multilayer.check_multilayer(args, {
        "xml": xml_common_dicts,
        "dep": dep_common_dicts
    })


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--xml-dir',
        default=j('..', 'xml'),
        help="Path to .xml output directory"
    )
    ap.add_argument(
        '--dep-dir',
        default=j('..', 'dep'),
        help="Path to .conllu output directory"
    )
    ap.add_argument(
        '--tsv-dir',
        default=j('..', 'coref', 'tsv'),
        help="Path to coreference .tsv output directory"
    )
    ap.add_argument(
        '--rst-dir',
        default=j('..', 'rst'),
        help="Path to RST .rs3 output directory"
    )
    ap.add_argument(
        '--unreliable-checks',
        help="By default, only validations that are guaranteed to never turn up false positives are run. "
             "If this flag is passed, validations that may turn up false positives will be run.",
        default=False,
        action='store_true'
    )

    main(ap.parse_args())