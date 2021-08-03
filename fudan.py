# fudan.py

from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Dict, Iterable, Tuple, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Session
from datetime import date, datetime

import json
import re

BASE_URL = 'http://www.gwz.fudan.edu.cn'


@dataclass
class Link:
    caption: str
    url: str
    clicks: int
    replies: int
    added: date

    @classmethod
    def from_row(cls, props: Dict[str, str], path: str) -> 'Link':
        clicks, replies = props['点击/回复'].split('/')
        # Skip number=int(props['编号']) - this only has meaning within one page

        return cls(
            caption=props['资源标题'],
            url=urljoin(BASE_URL, path),
            clicks=int(clicks),
            replies=int(replies),
            added=datetime.strptime(props['添加时间'], '%Y/%m/%d').date(),
        )

    def __str__(self):
        return f'{self.added} {self.url} {self.caption}'

    def author_title(self) -> Tuple[Optional[str], str]:
        sep = '：'  # full-width colon, U+FF1A

        if sep not in self.caption:
            return None, self.caption

        author, title = self.caption.split(sep, 1)
        author, title = author.strip(), title.strip()

        net_digest = '網摘'
        if author == net_digest:
            return None, self.caption

        return author, title


@dataclass
class Article:
    author: Optional[str]
    title: str
    date: date
    download: Optional[str]
    url: str
    publication: str = "復旦大學出土文獻與古文字研究中心學者文庫"

    @classmethod
    def from_link(cls, link: Link, download: str) -> 'Article':

        author, title = link.author_title()

        download = download.replace("\r", "").replace("\n", "").strip()
        if download == '#_edn1':
            download = None
        elif download[0] != '/':
            download = '/' + download

        return cls(
            author=author,
            title=title,
            date=link.added,
            download=download,
            url=link.url,
        )

    def __str__(self) -> str:
        return(
            f"\n作者   {self.author}"
            f"\n標題   {self.title}"
            f"\n發佈日期 {self.date}"
            f"\n下載連結 {self.download}"
            f"\n訪問網頁 {self.url}"
        )

    def as_dict(self) -> Dict[str, str]:
        return {
            'author': self.author,
            'title': self.title,
            'date': self.date.isoformat(),
            'download': self.download,
            'url': self.url,
            'publication': self.publication
        }


def compile_search_results(session: Session, links: Iterable[Link], category_filter: str) -> Iterable[Article]:

    for link in links:
        with session.get(link.url) as resp:
            resp.raise_for_status()
            doc = BeautifulSoup(resp.text, 'html.parser')

        category = doc.select_one('#_top td a[href="#"]').text
        if category != category_filter:
            continue

        content = doc.select_one('span.ny_font_content')
        dl_tag = content.find(
            'a', {
                'href': re.compile("/?(lunwen/|articles/up/).+")
            }
        )

        yield Article.from_link(link, download=dl_tag['href'])


def get_page(session: Session, query: str, page: int) -> Tuple[List[Link], int]:
    with session.get(
        urljoin(BASE_URL, '/Web/Search'),
        params={
            's': query,
            'page': page,
        },
    ) as resp:
        resp.raise_for_status()
        doc = BeautifulSoup(resp.text, 'html.parser')

    table = doc.select_one('#tab table')
    heads = [h.text for h in table.select('tr.cap td')]
    links = []

    for row in table.find_all('tr', class_=''):
        cells = [td.text for td in row.find_all('td')]
        links.append(Link.from_row(
            props=dict(zip(heads, cells)),
            path=row.find('a')['href'],
        ))

    page_td = doc.select_one('#tab table:nth-child(2) td')  # 共 87 条记录， 页 1/3
    n_pages = int(page_td.text.rsplit('/', 1)[1])

    return links, n_pages


def get_all_links(session: Session, query: str) -> Iterable[Link]:
    for page in count(1):
        links, n_pages = get_page(session, query, page)
        print(f'Scraping page {page}/{n_pages}')
        yield from links

        if page >= n_pages:
            break


def save_articles(articles: Iterable[Article], file_prefix: str) -> None:
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


def search(keyword):
    print("正在搜尋復旦大學出土文獻與古文字研究中心學者文庫……")
    print(f"關鍵字：「{keyword}」")
    with Session() as session:
        links = get_all_links(session, query=keyword)
        academic_library = '学者文库'
        articles = compile_search_results(
            session, links, category_filter=academic_library)
        # save_articles(articles, 'fudan_search_result')

        yield from articles


if __name__ == '__main__':
    search('尹誥')
