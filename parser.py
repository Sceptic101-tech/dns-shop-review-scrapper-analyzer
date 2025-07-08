from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time

def _change_main_window(driver):
    if len(driver.window_handles) == 2:
        original_window = driver.current_window_handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.close() # closing original operating window
                driver.switch_to.window(window_handle)
                break

def _get_first_search_suggestion(driver, query, uri_part):
    # finding the query line
    search = driver.find_element(By.ID, "text")
    search.clear()
    search.send_keys(query)
    search.send_keys(Keys.RETURN)
    time.sleep(random.randint(2,6))

    # get rid of locaton access notification
    driver.refresh()
    time.sleep(random.randint(2,6))

    return driver.find_element(By.PARTIAL_LINK_TEXT, uri_part)


def _access_page(driver, query, uri_search_part):
    attempts = 2
    for i in range(attempts):
        try:
            link = _get_first_search_suggestion(driver, query, uri_search_part)
            time.sleep(random.randint(2,6))
            link.click()
            time.sleep(random.randint(2,6))
        except:
            print('cant find interactive element :(')

        # in case 403 authorisation error
        if driver.title == 'HTTP 403':
            if i == attempts-1:
                return False
            print('Error 403. Trying open link in another tab')
            #open and switch to another tab
            driver.execute_script('''window.open("https://ya.ru","_blank");''')
            _change_main_window(driver)
        else:
            _change_main_window(driver)
            return True



def get_reviews_json(url):
    options = webdriver.ChromeOptions()

    # adding argument to disable the AutomationControlled flag
    options.add_argument('--disable-blink-features=AutomationControlled')

    # exclude the collection of enable-automation switches
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # turn-off userAutomationExtension
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument('--incognito')

    driver = webdriver.Chrome(options=options)

    try:
        driver.implicitly_wait(20)

        # changing the property of the navigator value for webdriver to undefined. That helps be invisible for some bot detectors
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.maximize_window()
        driver.get('https://ya.ru')
        time.sleep(random.randint(2,6))

        if not _access_page(driver, 'днс', 'dns-shop.ru'):
            print('Не удалось получить доступ к странице. Завершение работы')
            driver.quit()
            exit(-1)
        
        # closing excess windows
        original_window = driver.current_window_handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                driver.close()
                driver.switch_to.window(original_window)
                break
        
        time.sleep(20)

    finally:
        driver.quit()



if __name__ == '__main__':
    get_reviews_json('fdffd')