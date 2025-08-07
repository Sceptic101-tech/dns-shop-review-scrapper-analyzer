import os

class Config:
    # Пути
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    COOKIES_PATH =  os.path.join(DATA_DIR, 'cookies.pkl')
    REVIEWS_JSON_PATH = os.path.join(DATA_DIR, 'reviews.json')
    RAW_HTML_PATH = os.path.join(DATA_DIR, 'raw_html.txt')
    WORDCLOUD_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'wordcloud.png')

    # Параметры парсера
    # Верхняя и нижняя граница задержки перед осуществлением действия в браузере
    PARSER_WAITING_TIME_LB = 3
    PARSER_WAITING_TIME_UB = 8
    PARSER_MAX_RETRIES = 3

    # Браузер
    BROWSER_HEADLESS = False
    BROWSER_CITE_OPENNIG_ATTEMPS = 2
    BROWSER_DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads")
    BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Анализ
    ANALYZER_TO_LOWERCASE = False
    ANALYZER_REVIEW_LEN_TRESHOLD = 3
    ANALYZER_LANGUAGE = 'russian'
    ANALYZER_ERASE_PUNCTUATION = False
    ANALYZER_THRESHOLD_KEYWORD_SCORE = 0.5
    ANALYZER_TOP_N_KEYWORDS = 2
    ANALYZER_CONFIDENCE_TRESHOLD = 0.5
    ANALYZER_KEYPHRASE_NGRAM_RANGE = (2, 2)
    ANALYZER_KEYBERT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ANALYZER_KEYBERT_DIVERSITY = 0.7

    # WordCloud
    WORDCLOUD_WIDTH = 1000
    WORDCLOUD_HEIGHT = 1000
    WORDCLOUD_BACKGROUND_COLOR = "black"
    WORDCLOUD_COLORMAP = "Pastel1"
    WORDCLOUD_RANDOM_STATE = 42
    WORDCLOUD_COLLOCATIONS = True
    WORDCLOUD_MARGIN = 20