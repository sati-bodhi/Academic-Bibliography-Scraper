from base64 import b64encode
from datetime import date
from typing import Iterable, ClassVar, List, Dict

from attr import dataclass
from bs4 import BeautifulSoup, SoupStrainer, Tag
from requests import Session
import re
from itertools import count
from urllib.parse import urljoin

import uuid

BASE_URL = 'https://www.ctwx.tsinghua.edu.cn'

@dataclass
class Result:
    caption: str
    when: date
    path: str

    @classmethod
    def from_list_item(cls, item: Tag) -> 'Result':
        return cls(
            caption=item.a.text,
            path=item.a['href'],
            when=date.fromisoformat(item.find('span', recursive=False).text),
        )

    def as_dict(self) -> Dict[str, str]:
        return{
            "caption": self.caption,
            "url": urljoin(BASE_URL, self.path),
            "date": self.when.isoformat(),
        }

    def as_bib(self) -> Dict[str, str]:
        match_str = re.search("【出土文獻(第.+輯)】(.+)：(.+)", self.caption)
        if match_str:
            author = match_str.group(2)
            title = match_str.group(3)
            publication = "出土文獻"
            volume = match_str.group(1)

            id = uuid.uuid1()

            return{
                'ID': str(id.hex),
                'ENTRYTYPE': 'article',
                "author": author,
                "title": title,
                "journaltitle": publication,
                "volume": volume,
                "url": urljoin(BASE_URL, self.path)
            }

class TsinghuaSite:
    subdoc: ClassVar[SoupStrainer] = SoupStrainer(name='ul', class_='search_list')
    pagination: ClassVar[SoupStrainer] = SoupStrainer(name='table', class_='listFrame')

    def __init__(self):
        self.session = Session()

    def __enter__(self) -> 'TsinghuaSite':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def search(self, query: str) -> Iterable[List]:
        with self.session.post(
            urljoin(BASE_URL, 'search.jsp'),
            params={'wbtreeid': 1001},
            data={
                'lucenenewssearchkey': b64encode(query.encode()),
                '_lucenesearchtype': '1',
                'searchScope': '0',
                'x': '0',
                'y': '0',
            },
        ) as resp:

            resp.raise_for_status()
            pages = BeautifulSoup(markup=resp.text, features='html.parser', parse_only=self.pagination)
            n_pages_string = list(pages.select_one('td').children)[4]
            n_pages = int(re.search(r'\d+', n_pages_string)[0])

            if n_pages > 1:
                docs = []

                for page in count(1):
                    with self.session.get(
                        urljoin(BASE_URL, 'search.jsp'),
                        params={
                            'wbtreeid': 1001,
                            'newskeycode2': b64encode(query.encode()),
                            'searchScope': '0',
                            'currentnum': page,
                        },
                    ) as resp:

                        resp.raise_for_status()
                        doc = BeautifulSoup(markup=resp.text, features='html.parser', parse_only=self.subdoc)
                        print(f"Scraping page {page}/{n_pages}.")
                        docs.append(doc)

                    if page >= n_pages:
                        yield from docs
                        break

                else:
                    doc = BeautifulSoup(markup=resp.text, features='html.parser', parse_only=self.subdoc)
                    yield doc


    def yield_results(self, query) -> Iterable[Result]:
        doc_gen = self.search(query)
        for doc in doc_gen:
            for item in doc.find('ul', recursive=False).find_all('li', recursive=False):
                yield Result.from_list_item(item)


def search(keyword):
    with TsinghuaSite() as site:
        query = keyword
        results = tuple(site.yield_results(query))

    yield from results

def main():

    results = search('尹至')

    # assert any(query in r.caption for r in results)
    for result in results:
        print(result)


if __name__ == '__main__':
    main()