import os

import mecab


def refine(title: str):
    """Refine the project name."""
    refined = title.lower()
    with open('./refine.txt', 'r') as file:
        for line in file:
            tokens = line.split('\t')
            src = tokens[0]
            if tokens[1].endswith('\n'):
                dst = ''
            else:
                dst = tokens[1]
            refined = refined.replace(src, dst).strip().replace('  ', ' ')
    return refined


def tokenize(title: str):
    """Tokenize and extract unique nouns from the project name."""
    parser = mecab.MeCab()
    tokens = parser.nouns(title)
    tokens = ' '.join(list(set(tokens)))
    return tokens