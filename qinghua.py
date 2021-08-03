from contextlib import contextmanager
from dataclasses import dataclass, asdict, replace
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Optional, ContextManager
import re
import os
import time
import json

# pip install proxy.py
import proxy
from proxy.http.exception import HttpRequestRejected
from proxy.http.parser import HttpParser
from proxy.http.proxy import HttpProxyBasePlugin
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class PrimaryResult:
    captions: str
    date: date
    link: str
    publication:str = "清華大學出土文獻研究與保護中心"

    @classmethod
    def from_row(cls, row: WebElement) -> 'PrimaryResult': 

        caption_elems = row.find_element_by_tag_name('a')
        date_elems = row.find_element_by_class_name('time')

        published_date = date.isoformat(datetime.strptime(date_elems.text, '%Y-%m-%d'))

        return cls(
            captions = caption_elems.text,
            date = published_date,
            link = caption_elems.get_attribute('href'),
        )

    def as_dict(self):
        return{
            "caption": self.captions,
            "date": self.date,
            "url": self.link,
        }

    def __str__(self):
        return (
            f'\n標題     {self.captions}'
            f'\n發表時間  {self.date}'
            f'\n文章連結　{self.link}'
        )


class MainPage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
 
    def submit_search(self, keyword: str) -> None:
        driver = self.driver
        wait = WebDriverWait(self.driver, 100)

        xpath = "//form/button/input"
        element_to_hover_over = driver.find_element_by_xpath(xpath)
        hover = ActionChains(driver).move_to_element(element_to_hover_over)
        hover.perform()

        search = wait.until(
            EC.presence_of_element_located((By.ID, 'showkeycode1015273'))
        )
        search.send_keys(keyword)
        search.submit()


    def get_element_and_stop_page(self, *locator) -> WebElement:
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)
        wait = WebDriverWait(self.driver, 30, ignored_exceptions=ignored_exceptions)
        elm = wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("window.stop();")
        return elm

    def next_page(self) -> None:
        try: 
            link = self.get_element_and_stop_page(By.LINK_TEXT, "下一页")
            link.click()
            print("Navigating to Next Page")

        except (TimeoutException, WebDriverException):
            print("No button with 「下一页」 found.")
            return 0


    # @contextmanager
    # def wait_for_new_window(self):
    #     driver = self.driver
    #     handles_before = driver.window_handles
    #     yield
    #     WebDriverWait(driver, 10).until(
    #         lambda driver: len(handles_before) != len(driver.window_handles))

    def switch_tabs(self):
        driver = self.driver
        print("Current Window:")
        print(driver.title)
        print()

        p = driver.current_window_handle
        
        chwd = driver.window_handles
        time.sleep(3)
        driver.switch_to.window(chwd[1])

        print("New Window:")
        print(driver.title)
        print()


class SearchResults:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get_primary_search_result(self):
        
        filePath = os.path.join(os.getcwd(), "qinghua_primary_search_result.json")

        if os.path.exists(filePath):
            os.remove(filePath)

        rows = self.driver.find_elements_by_xpath('//ul[@class="search_list"]/li')

        for row in rows:
            rslt = PrimaryResult.from_row(row)
            with open('qinghua_primary_search_result.json', 'a') as file:
                json.dump(asdict(rslt), file, ensure_ascii=False, indent=4)
            yield rslt


# class ContentFilterPlugin(HttpProxyBasePlugin):
#     HOST_WHITELIST = {
#         b'ocsp.digicert.com',
#         b'ocsp.sca1b.amazontrust.com',
#         b'big5.oversea.cnki.net',
#         b'gwz.fudan.edu.cn',
#         b'bsm.org.cn/index.php'
#         b'ctwx.tsinghua.edu.cn',
#     }

#     def handle_client_request(self, request: HttpParser) -> Optional[HttpParser]:
#         host = request.host or request.header(b'Host')
#         if host not in self.HOST_WHITELIST:
#             raise HttpRequestRejected(403)

#         if any(
#             suffix in request.path
#             for suffix in (
#                 b'png', b'ico', b'jpg', b'gif', b'css',
#             )
#         ):
#             raise HttpRequestRejected(403)

#         return request

#     def before_upstream_connection(self, request):
#         return super().before_upstream_connection(request)
#     def handle_upstream_chunk(self, chunk):
#         return super().handle_upstream_chunk(chunk)
#     def on_upstream_connection_close(self):
#         pass


# @contextmanager
# def run_driver() -> ContextManager[WebDriver]:
#     prox_type = ProxyType.MANUAL['ff_value']
#     prox_host = '127.0.0.1'
#     prox_port = 8889

#     profile = FirefoxProfile()
#     profile.set_preference('network.proxy.type', prox_type)
#     profile.set_preference('network.proxy.http', prox_host)
#     profile.set_preference('network.proxy.ssl', prox_host)
#     profile.set_preference('network.proxy.http_port', prox_port)
#     profile.set_preference('network.proxy.ssl_port', prox_port)
#     profile.update_preferences()

#     plugin = f'{Path(__file__).stem}.{ContentFilterPlugin.__name__}'

#     with proxy.start((
#         '--hostname', prox_host,
#         '--port', str(prox_port),
#         '--plugins', plugin,
#     )), Firefox(profile) as driver:
#         yield driver


def search(keyword) -> None:
    print("正在搜尋清華大學出土文獻研究與保護中心網……")
    print(f"關鍵字：「{keyword}」")
    with Firefox() as driver:
        driver.get('http://www.ctwx.tsinghua.edu.cn/index.htm')

        page = MainPage(driver)
        # page.select_dropdown_item()
        page.submit_search(keyword)

        time.sleep(5)
        # page.switch_tabs()

        while True:
            primary_result_page = SearchResults(driver)
            primary_results = primary_result_page.get_primary_search_result()
            
            yield from primary_results
            
            # for result in primary_results:
            #     print(result)
            #     print()
                
            if page.next_page() == 0:
                break
            else:
                pass


if __name__ == '__main__':
    search('尹至')