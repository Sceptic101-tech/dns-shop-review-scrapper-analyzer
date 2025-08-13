import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import Config
import random
import time
import os.path

# TODO mimicking a human reaction for actions

WAITING_TIME_LB, WAITING_TIME_UB = (Config.PARSER_WAITING_TIME_LB, Config.PARSER_WAITING_TIME_UB)

class BrowserManager:
    def __init__(self, headless):
        # dont use with undetected_chromedriver, it does this things automaticly
                #self.driver_options = webdriver.ChromeOptions()
                # # adding argument to disable the AutomationControlled flag
                # self.driver_options.add_argument('--disable-blink-features=AutomationControlled')

                # # exclude the collection of enable-automation switches
                # self.driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])

                # # turn-off userAutomationExtension
                # self.driver_options.add_experimental_option("useAutomationExtension", False)

                # self.driver_options.add_argument('--incognito')
                # self.browser = uc.Chrome(options=self.driver_options)

                # changing the property of the navigator value for webdriver to undefined. That helps be invisible for some bot detectors
                # self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.browser = uc.Chrome(headless=headless)
        self.browser.implicitly_wait(5)
        self.browser.maximize_window()
        time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))

    def _change_main_window(self):
        if len(self.browser.window_handles) > 1:
            original_window = self.browser.current_window_handle
            for window_handle in self.browser.window_handles:
                if window_handle != original_window:
                    self.browser.switch_to.window(window_handle)
                    break

    def _close_excess_windows(self):
        if len(self.browser.window_handles) > 1:
            original_window = self.browser.current_window_handle
            for window_handle in self.browser.window_handles:
                if window_handle != original_window:
                    self.browser.switch_to.window(window_handle)
                    self.browser.close()
                    self.browser.switch_to.window(original_window)
    
    def write_cookies(self, filename : str):
        with open(filename, 'w') as file:
            cookies = self.browser.get_cookies()
            file.write(cookies)
    
    def read_cookies(self, filename : str):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                cookies = file.read()
                self.browser.add_cookie(cookies)

    # def __del__(self):
    #     self.browser.quit()

class NavigationManager:
    def __init__(self, browser : BrowserManager):
        self.browser_manager = browser
    
    def _handle_403_error(self):
        self.browser_manager.browser.execute_script('''window.open("https://ya.ru","_blank");''')
        self.browser_manager._change_main_window()
        time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
        self.browser_manager._close_excess_windows()

    # finding the query line and enters the query. Works only for Yandex search
    def _enter_query(self, query):
        search = self.browser_manager.browser.find_element(By.ID, "text")
        search.clear()
        search.send_keys(query)
        time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
        search.send_keys(Keys.RETURN)

    # GET query with 403_error handle 
    def try_open_page(self, url, attempts=2):
        for i in range(attempts):
            self.browser_manager.browser.get(url)
            # in case of an 403 authorisation error, try to open a new tab and try again.
            if 'HTTP 403' in self.browser_manager.browser.page_source:
                if i == attempts-1:
                    print('Couldnt open the page in the specified number of attempts')
                    return False
                print(f'Error 403. Trying open link in another tab. Attempt {i+1}')
                self._handle_403_error()
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
            else:
                return True

    # The main idea is to create a website cookie by visiting it through a search. This helps to bypass the bot check
    def try_open_page_via_search(self, search_query, url_part, attempts=2):
        # search_query example: 'днс'
        # url_part example: 'dns-shop.ru'
        for i in range(attempts):
            self.browser_manager.browser.get('https://ya.ru')
            time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
            try:
                self._enter_query(search_query)
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))

                # button with dumb suggestions may appear, this will help us get rid of it.
                notification_close_button = WebDriverWait(self.browser_manager.browser, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.Distribution-ButtonClose')))
                notification_close_button.click()
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))

                # looking for url, that matches url_part
                link = self.browser_manager.browser.find_element(By.PARTIAL_LINK_TEXT, url_part)
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
                link.click()
                self.browser_manager._change_main_window()
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
                self.browser_manager._close_excess_windows()
            except:
                print('Cant find interactive element :(')

            # in case of an 403 authorization error, opening a new tab and try again
            if 'HTTP 403' in self.browser_manager.browser.page_source:
                if i == attempts-1:
                    print('Couldnt open the page in the specified number of attempts')
                    return False
                print(f'Error 403. Trying open link in another tab. Attempt {i+1}')
                self._handle_403_error()
                time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
            else:
                return True

class ParseHelper:
    def __init__(self, browser : BrowserManager):
        self.browser_manager = browser

    def get_page_raw_html(self) -> str:
        return self.browser_manager.browser.page_source
    
    def page_to_txt(self, file_name):
        with open(file_name, 'w', encoding='utf-8') as file:
            raw_html = self.get_page_raw_html()
            file.write(raw_html)

class DNS_Shop_Parser:
    def __init__(self, headless : bool=False):
        self.browser_manager = BrowserManager(headless=headless)
        self.navigator = NavigationManager(self.browser_manager)
        self.parse_helper = ParseHelper(self.browser_manager)
        self.successful_open=False
    
    def how_to_use(self):
        return '''
                1. Create an instance of the DNS_parser object (this has already been done)
                2. Use the /.open_DNS_site()/ method to avoid bot-checking for access to the DNS-site
                3.1. Use the /.get_product_reviews('product_reviews_url')/ to get reviews in list of dictionaries format
                3.2. Use the /parse_helper.page_to_txt()/ method to get raw html code in .txt file'''

    # works only for dns_review page
    def show_more_reviews(self, desired_review_cnt):
        button_click_cnt = (desired_review_cnt-4)//10 + 1 # magic number. Each button click produces 10 reviews. There is only 4 reviews displayed at the beggining
        for _ in range(button_click_cnt):
            time.sleep(random.randint(WAITING_TIME_LB, WAITING_TIME_UB))
            try:
                # show_more_button = self.browser_manager.browser.find_element(By.CSS_SELECTOR, "button.paginator-widget__more")
                show_more_button = WebDriverWait(self.browser_manager.browser, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.paginator-widget__more')))
                show_more_button.click()
            except:
                print('Couldnt get the desired number of reviews')
    
    def extract_reviews(self, raw_html) -> list:
        soup = BeautifulSoup(raw_html, 'html.parser')

        # search for all reviews. Depends on the page source code. We will get a list with all the reviews on the page.
        # 'ow-opinion__texts' contains lables(Достоинства, Недостатки, ...) and user comments block
        all_reviews = soup.find_all('div', 'ow-opinion__texts', recursive=True)
        parsed_reviews = []
        for review in all_reviews:
            title_part = review.find_all('div', 'ow-opinion__text-title') # extracting only "pros" and "cons" labels
            desc_part = review.find_all('div', 'ow-opinion__text-desc') # extracting only user comments
            parsed_reviews.append({'Достоинства' : None, 'Недостатки' : None, 'Комментарий' : None, 'Фото' : None}) # not a bug, just feature
            for el in zip(title_part, desc_part):
                parsed_reviews[-1][el[0].text] = el[1].text # merging label with comments to dictionary as key and value
        return parsed_reviews # list of dict, each element is review
    
    def open_DNS_site(self):
        if self.navigator.try_open_page_via_search('днс', 'dns-shop.ru'):
            self.successful_open=True

    def get_product_reviews(self, url_review_page, desired_review_cnt):
        self.navigator.try_open_page(url_review_page)
        self.show_more_reviews(desired_review_cnt)
        raw_html = self.parse_helper.get_page_raw_html()
        return self.extract_reviews(raw_html)
    
__all__ = ['DNS_Shop_Parser']