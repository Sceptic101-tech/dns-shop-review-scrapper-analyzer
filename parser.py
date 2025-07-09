from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
import time


class DNS_SHOP_Parser:
    def __init__(self):
        self.driver_options = webdriver.ChromeOptions()
        # adding argument to disable the AutomationControlled flag
        self.driver_options.add_argument('--disable-blink-features=AutomationControlled')

        # exclude the collection of enable-automation switches
        self.driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # turn-off userAutomationExtension
        self.driver_options.add_experimental_option("useAutomationExtension", False)

        self.driver_options.add_argument('--incognito')

        self.driver = webdriver.Chrome(options=self.driver_options)
        self.driver.implicitly_wait(5)

        # changing the property of the navigator value for webdriver to undefined. That helps be invisible for some bot detectors
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
        self.driver.get('https://ya.ru')


    def how_to_use(self):
        return'''
                1. Create an instance of the DNS_parser object (this has already been done)
                2. Use the /try_open_page_through_search()/ method to avoid bot-checking for access to the DNS-site. This will take you to the required feedback page.
                3. Use the /show_more_reviews()/ method to display around N reviews on the page.
                4. Get the html code of the page using /get_page_raw_html()/
                5. Extract reviews from the html with /extract_reviews()/. It return list of dictionaries, so you can easily put it into DataFrame
                6. Quit session with  /quit()/'''


    def _change_main_window(self):
        if len(self.driver.window_handles) > 1:
            original_window = self.driver.current_window_handle
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.close() # closing original operating window
                    self.driver.switch_to.window(window_handle)
                    break


    def _close_excess_windows(self):
        if len(self.driver.window_handles) > 1:
            original_window = self.driver.current_window_handle
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    self.driver.close()
                    self.driver.switch_to.window(original_window)


    def _enter_query(self, query):
        # finding the query line. Works only for Yandex search
        search = self.driver.find_element(By.ID, "text")
        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.RETURN)
        time.sleep(random.randint(4,8))
        # trying to get rid of the dumb notifications
        self.driver.refresh()


    def try_open_page(self, url, attempts=2):
        for i in range(attempts):
            self.driver.get(url)
            # in case of an 403 authorisation error, try to open a new tab and try again.
            if 'HTTP 403' in self.driver.page_source:
                if i == attempts-1:
                    print('Couldnt open the page in the specified number of attempts')
                    return False
                print(f'Error 403. Trying open link in another tab. Attempt {i+1}')
                self.driver.execute_script('''window.open("https://ya.ru","_blank");''')
                self._change_main_window()
                self._close_excess_windows()
                time.sleep(random.randint(2,4))
            else:
                self._change_main_window()
                return True


    # The main idea is to create a website cookie by visiting it through a search. This helps to bypass the bot check
    def try_open_page_through_search(self, search_query, url_part, desired_url, attempts=2):
        # search_query example: 'днс'
        # url_part example: 'dns-shop.ru'
        for i in range(attempts):
            self.driver.get('https://ya.ru')
            time.sleep(random.randint(2,4))
            try:
                self._enter_query(search_query)
                time.sleep(random.randint(4,8))
                link = self.driver.find_element(By.PARTIAL_LINK_TEXT, url_part)
                time.sleep(random.randint(4,6))
                link.click()
                time.sleep(random.randint(4,6))
            except:
                print('Cant find interactive element :(')

            # in case of an 403 authorization error, try to open a new tab and try again
            if 'HTTP 403' in self.driver.page_source:
                if i == attempts-1:
                    print('Couldnt open the page in the specified number of attempts')
                    return False
                print(f'Error 403. Trying open link in another tab. Attempt {i+1}')
                self.driver.execute_script('''window.open("https://ya.ru","_blank");''')
                self._change_main_window()
                self._close_excess_windows()
                time.sleep(random.randint(4,6))
            else:
                self._change_main_window()
                time.sleep(random.randint(4,6))
                return self.try_open_page(desired_url, attempts=1)


    # works only for dns_review page
    def show_more_reviews(self, desired_review_cnt):
        button_click_cnt = (desired_review_cnt-4)//10 + 1
        for _ in range(button_click_cnt):
            time.sleep(random.randint(3,7))
            try:
                show_more_button = self.driver.find_element(By.CSS_SELECTOR, "button.paginator-widget__more")
                show_more_button.click()
            except:
                print('Couldnt get the desired number of reviews')


    def get_page_raw_html(self):
        return self.driver.page_source


    def page_to_txt(self, file_name):
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(self.get_page_raw_html())
    
    
    def extract_reviews(self, raw_html):
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
                parsed_reviews[-1][el[0].text] = el[1].text.replace(';', '\n') # merging label with comments to dictionary as key and value
        return parsed_reviews # list of dict, each element is review


    def quit(self):
        self.driver.quit()


    def __del__(self):
        self.driver.quit()