from dataclasses import dataclass, asdict
from itertools import count
from typing import Dict, Iterable, Tuple, List

from bs4 import BeautifulSoup
from requests import post
from datetime import date, datetime

import json
import os
import re

@dataclass
class Result:
    author: str
    title: str
    date: date
    url: str
    publication: str = "武漢大學簡帛網"

    @classmethod
    def from_metadata(cls, metadata: Dict) -> 'Result': 
        author = metadata['caption'].split('：',1)[0]
        title = metadata['title']
        published_date = datetime.strptime(metadata['date'], '%y/%m/%d').date()
        url = 'http://www.bsm.org.cn/' + metadata['url']

        return cls(
            author = author,
            title = title,
            date = published_date,
            url = url
        )


    def __str__(self):
        return (
            f'作者　　　　{self.author}'
            f'\n標題     {self.title}'
            f'\n發表時間  {self.date.isoformat()}'
            f'\n文章連結　{self.url}'
            f'\n發表平台  {self.publication}'
        )


    def as_dict(self) -> Dict[str, str]:
        return {
            'author': self.author,
            'title': self.title,
            'date': self.date.isoformat(),
            'url': self.url,
            'publication': self.publication,
        }


def submit_query(keyword: str):
    print("正在搜尋武漢大學簡帛網……")
    print(f"關鍵字：「{keyword}」")
    query = {"searchword": keyword}
    with post('http://www.bsm.org.cn/pages.php?pagename=search', query) as resp:
        resp.raise_for_status()
        doc = BeautifulSoup(resp.text, 'html.parser')
        content = doc.find('div', class_='record_list_main')
        rows = content.select('ul')


    for row in rows:
        if len(row.findAll('li')) != 2:
            print()
            print(row.text)
            print()
        else:
            captions_tag, date_tag = row.findAll('li')
            caption_anchors = captions_tag.findAll('a')
            category, caption = [item.text for item in caption_anchors]
            url = caption_anchors[1]['href']
            # print(caption_anchors[1].attrs)
            meta = caption_anchors[1]['title']
            published_date = re.sub("[()]", "", date_tag.text)
            try:
                title = re.search("文章標題：(.+)\r", meta).group(1)
            except:
                title = caption.split("：",1)[1]

            yield {
                "category": category,
                "caption": caption,
                "title": title, 
                "date": published_date,
                "url": url,}


def remove_json_if_exists(filename):
    json_file = filename + ".json"
    filePath = os.path.join(os.getcwd(), json_file)

    if os.path.exists(filePath):
        os.remove(filePath)


def search(query: str):
    # remove_json_if_exists('wuhan_search_result')
    rslt = submit_query(query)
    # yield from rslt

    for metadata in rslt:
        article = Result.from_metadata(metadata)
        yield article

        # print(article)
        # print()

        # with open('wuhan_search_result.json', 'a') as file:
        #     json.dump(asdict(article), file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    search('郭店')