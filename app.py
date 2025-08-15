from flask import Flask, url_for, render_template, request, redirect, current_app
from scripts import error_codes_dict # __init__.py
from config import Config
import time
from scripts.parser_pool import ParserPool
from keybert import KeyBERT
import scripts.text_processing as tp
import scripts.analyzer as text_analyzer
from scripts.vizualizer import WordCloudGenerator
from config import Config

# TODO Инициализация модели для анализа должна происходить только один раз, при запуске приложения
# TODO Сделать пул парсеров(обьектов DNS_Shop_Parser), а не создавать каждый раз новый обьект при вводе данных пользователем
# TODO Дополнить код комментариями
# TODO Обработка исключений
# TODO Обработка исключения, если пул парсеров пуст(Empty exception)

app = Flask(__name__, template_folder='templates')

keybert_model = KeyBERT(Config.ANALYZER_KEYBERT_MODEL_NAME)

parser_pool = ParserPool(size=Config.PARSER_POOL_SIZE, block=Config.PARSER_POOL_BLOCK,
                         timeout=Config.PARSER_POOL_TIMEOUT, browser_headless=Config.BROWSER_HEADLESS)

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
    parser = parser_pool.get()
    try:
        if parser is None:
            redirect(url_for('error'), code=520)
        
        # if not parser.successful_open:
        #     parser.open_DNS_site() # execute once
        # reviews = parser.get_product_reviews(review_url, review_cnt) # propper form: list of dictionaries
        reviews = []
        with open(Config.RAW_HTML_PATH, 'r', encoding='utf-8') as file:
            reviews = parser.extract_reviews(file.read()) # propper form: list of dictionaries
        
        positive_list, negative_list = tp.split_positive_negative_parts(reviews, Config.ANALYZER_MIN_REVIEW_LEN_TRESHOLD)

        positive_list = tp.preprocess_list_of_texts(positive_list, 
                                                    to_lower=Config.ANALYZER_TO_LOWERCASE, 
                                                    erase_punct=Config.ANALYZER_ERASE_PUNCTUATION)
        
        negative_list = tp.preprocess_list_of_texts(negative_list, 
                                                    to_lower=Config.ANALYZER_TO_LOWERCASE, 
                                                    erase_punct=Config.ANALYZER_ERASE_PUNCTUATION)

        positive_raw_keywords_list = text_analyzer.extract_keyphrases(positive_list, keybert_model, 
                                                                      Config.ANALYZER_TOP_N_KEYWORDS, 
                                                                      Config.ANALYZER_KEYPHRASE_NGRAM_RANGE)
        positive_keywords_dict = text_analyzer.get_dict_keyphrases(positive_raw_keywords_list)
        
        negative_raw_keywords_list = text_analyzer.extract_keyphrases(negative_list, keybert_model, 
                                                                      Config.ANALYZER_TOP_N_KEYWORDS, 
                                                                      Config.ANALYZER_KEYPHRASE_NGRAM_RANGE)
        negative_keywords_dict = text_analyzer.get_dict_keyphrases(negative_raw_keywords_list)

        WordCloudGenerator.generate(positive_keywords_dict, Config.POSITIVE_IMAGE_PATH, save_image=True)
        WordCloudGenerator.generate(negative_keywords_dict, Config.NEGATIVE_IMAGE_PATH, save_image=True)

    except Exception as ex:
       app.logger.exception('Ошибка при анализе: %s', ex)
       return redirect(url_for('error'), code=1)
    
    finally:
        if parser_pool.put(parser) is None:
            return redirect(url_for('error'), code=521)
        else:
            return redirect(url_for('results'))

  
@app.route('/results', methods=['GET'])
def results():
   return render_template('results.html', positive_img_src="static/positive.png", negative_img_src="static/negative.png")

@app.route('/error', methods=['GET'])
def error():
    error_code = request.args.get('code')
    if error_code in error_codes_dict:
        return render_template('error.html', error_cause=error_codes_dict[error_code])
    else:
        return render_template('error.html', error_cause=error_codes_dict[1])

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=42960, debug=False)
    app.run(debug=True)
