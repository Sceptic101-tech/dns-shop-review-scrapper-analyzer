from parser import DNS_Shop_Parser
import pandas as pd

parser = DNS_Shop_Parser()

print(parser.how_to_use())

parser.open_DNS_site()
reviews = parser.get_product_reviews('https://www.dns-shop.ru/product/opinion/7ffd0cf6a89cd21a/667-smartfon-xiaomi-redmi-note-14-256-gb-cernyj/', desired_review_cnt=100)

parser.parse_helper.page_to_txt('example.txt')

df = pd.DataFrame(reviews)

print(df.info())