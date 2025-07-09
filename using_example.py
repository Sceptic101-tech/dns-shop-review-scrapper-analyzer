from parser import DNS_SHOP_Parser
import pandas as pd

parser = DNS_SHOP_Parser()

print(parser.how_to_use())

search_query = 'днс'
url_part = 'dns-shop.ru'
desired_url = 'https://www.dns-shop.ru/product/opinion/3ed66c69e7cbed20/dekorativnyj-svetilnik-xiaomi-light-bar-cernyj/'

if not parser.try_open_page_through_search(search_query, url_part, desired_url):
    exit(-1)

parser.show_more_reviews(120)

raw_html = parser.get_page_raw_html()
parser.page_to_txt('test_120_rev.txt')

reviews = parser.extract_reviews(raw_html)

parser.quit()

df = pd.DataFrame(reviews)