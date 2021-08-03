import cnki, fudan, wuhan, qinghua
import json
from typing import Iterable, Tuple, List
from pathlib import Path


DB_DICT = {
    "cnki": cnki.search,
    "fudan": fudan.search,
    "wuhan": wuhan.search,
    "qinghua": qinghua.search,
    }


def save_articles(articles: Iterable, file_prefix: str) -> None:
    file_path = Path(file_prefix).with_suffix('.json')

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
    rslt = search(['郭店', '尹至'],'qinghua', 'wuhan')
    save_articles(rslt, 'search_result')