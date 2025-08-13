from flask import Flask, url_for, render_template, request, redirect
from config import Config
import time
from scripts.parser import DNS_Shop_Parser
from keybert import KeyBERT
from pymystem3 import Mystem
from wordcloud import WordCloud
import scripts.text_processing as tp
import scripts.analyzer as text_analyzer
from scripts.vizualizer import WordCloudGenerator
from config import Config
# import multiprocessing as mp
# import nltk
import re
import os

app = Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    """Главная страница – форма ввода URL и количества отзывов."""
    if request.method == 'POST':
        review_url = request.form['review_url']
        review_cnt = int(request.form['review_cnt'])
        return redirect(url_for('analyzing', review_url=review_url, review_cnt=review_cnt))
    else:
        return render_template(
            'index.html',
            min_reviews_value=Config.PARSER_REVIEWS_LB,
            max_review_value=Config.PARSER_REVIEWS_UB
        )

@app.route('/analyzing', methods=['GET'])
def analyzing():
    review_url = request.args.get('review_url')
    review_cnt = int(request.args.get('review_cnt'))
    try:
        parser = DNS_Shop_Parser(headless=Config.BROWSER_HEADLESS)
        # if not parser.successful_open:
        #     parser.open_DNS_site() # execute once
        # reviews = parser.get_product_reviews(review_url, review_cnt) # propper form: list of dictionaries
        reviews = []
        with open(Config.RAW_HTML_PATH, 'r', encoding='utf-8') as file:
            reviews = parser.extract_reviews(file.read()) # propper form: list of dictionaries
        
        positive_list, negative_list = tp.split_positive_negative_parts(reviews, Config.ANALYZER_REVIEW_LEN_TRESHOLD)

        positive_list = tp.preprocess_list_of_texts(positive_list, to_lower=Config.ANALYZER_TO_LOWERCASE, erase_punct=Config.ANALYZER_ERASE_PUNCTUATION)
        negative_list = tp.preprocess_list_of_texts(negative_list, to_lower=Config.ANALYZER_TO_LOWERCASE, erase_punct=Config.ANALYZER_ERASE_PUNCTUATION)

        model = KeyBERT(Config.ANALYZER_KEYBERT_MODEL_NAME)

        positive_raw_keywords_list = text_analyzer.extract_keyphrases(positive_list, model, Config.ANALYZER_TOP_N_KEYWORDS, Config.ANALYZER_KEYPHRASE_NGRAM_RANGE)
        positive_keywords_dict = text_analyzer.get_dict_keyphrases(positive_raw_keywords_list)
        negative_raw_keywords_list = text_analyzer.extract_keyphrases(negative_list, model, Config.ANALYZER_TOP_N_KEYWORDS, Config.ANALYZER_KEYPHRASE_NGRAM_RANGE)
        negative_keywords_dict = text_analyzer.get_dict_keyphrases(negative_raw_keywords_list)

        positive_img = WordCloudGenerator.generate(positive_keywords_dict, Config.POSITIVE_IMAGE_PATH, save_image=True)
        negative_img = WordCloudGenerator.generate(negative_keywords_dict, Config.NEGATIVE_IMAGE_PATH, save_image=True)

        return redirect(url_for('results'))

    except Exception as ex:
       app.logger.exception('Ошибка при анализе: %s', ex)
       print('Some error occured')
       return redirect(url_for('error'))

  
@app.route('/results', methods=['GET'])
def results():
   return render_template('results.html', positive_img_src="static/positive.png", negative_img_src="static/negative.png")

if __name__ == "__main__":
    app.run(debug=True)
    # app.run()

@app.route('/error', methods=['GET'])
def error():
    return render_template('error.html')