import cnki, fudan, wuhan, qinghua
import json
from typing import Iterable, Tuple, List
from pathlib import Path

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

DB_DICT = {
    "cnki": cnki.search,
    "fudan": fudan.search,
    "wuhan": wuhan.search,
    "qinghua": qinghua.search,
    }

def save_articles(articles: Iterable, file_prefix: str, output_format: str) -> None:
    file_path = Path(file_prefix).with_suffix(f'.{output_format}')

    if output_format == "json":

        with file_path.open('w') as file:
            file.write('[\n')
            first = True

            for article in articles:

                if first:
                    first = False
                else:
                    file.write(',\n')
                json.dump(article.as_dict(), file, ensure_ascii=False, indent=4)

            file.write('\n]\n')

    elif output_format == "bib":

        db = BibDatabase()

        for article in articles:
            if article.as_bib():
                bib_dict = article.as_bib()
                bib_dict = {k: v for k, v in bib_dict.items() if v is not None}  # Remove none values.
                db.entries.append(bib_dict)

        writer = BibTexWriter()

        with file_path.open('w') as bibfile:
            bibfile.write(writer.write(db))


def db_search(keyword: str, *args: Tuple[str]):

    if args:
        
        for db in args:
            yield from DB_DICT[db](keyword)

    else:

        for key in DB_DICT.keys():
            yield from DB_DICT[key](keyword)


def search(keywords: List[str], *args: str):
    for kw in keywords:
        yield from db_search(kw, *args)


if __name__ == '__main__':
    rslt = search(['尹至'], 'cnki', 'wuhan', 'qinghua')
    save_articles(rslt, 'search_result', 'bib')