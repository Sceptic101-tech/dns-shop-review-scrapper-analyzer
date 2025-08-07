import re
import nltk
from keybert import KeyBERT
from pymystem3 import Mystem

# Принимает список словарей, возвращает список строк, сконкатенированных частей отзыва.
def convert_to_list_of_reviews(reviews, review_len_treshold = 2):
    dict_of_none = {'Достоинства' : None, 'Недостатки' : None, 'Комментарий' : None, 'Фото' : None}
    texts = []
    for review in reviews:
        if review != dict_of_none:
            texts.append('') # if all the values in review is None, but if it has some key, that is not in dict_of_none -> memory leak. need to fix that
            for key, value in review.items():
                if (value is not None) and (key in dict_of_none.keys()) and (len(value.split(' ')) > review_len_treshold):
                    texts[-1] += ' ' + value + ' '
    return texts

# Принимает список словарей, возвращает два списка строк - позитивные и неготивные отзывы
def split_positive_negative_parts(reviews : list, review_len_treshold = 2) -> tuple[list, list]:
    dict_of_none = {'Достоинства' : None, 'Недостатки' : None, 'Комментарий' : None, 'Фото' : None}
    positive_list = []
    negative_list = []
    for review in reviews:
        if review != dict_of_none:
            for key, value in review.items():
                if (value is not None) and (len(value.split(' ')) > review_len_treshold):
                    if key == 'Достоинства':
                        positive_list.append(value)
                    if key == 'Недостатки':
                        negative_list.append(value)
                    else:
                        break
    return (positive_list, negative_list)

# Препроцессинг текста
def preprocess_list_of_texts(list_of_texts : list[str], to_lower=True, erase_punct=False) -> list:
    cleadned_list = []
    for idx, text in enumerate(list_of_texts):
        cleadned_list.append(text.lower() if to_lower else text)
        if erase_punct:
            cleadned_list[idx] = re.sub(r'[^\w\s]', ' ', cleadned_list[idx])
    return cleadned_list

# Возможность пердварительной лемматизации отзывов, перед извлечением ключевых N-грамм
def get_lemmatized_text(list_of_texts, mystem: Mystem) -> list:
    lemmatized_texts = []
    for text in list_of_texts:
        lemmatized_texts.append(''.join(mystem.lemmatize(text)))
    return lemmatized_texts

# Извлечение ключевых N-грамм из каждого отзыва
def extract_keyphrases(corpus_list : list[str], model : KeyBERT, top_n=2, keyphrase_ngram_range=(1,2)) -> list:
    raw_keywords_list = []
    for corpus in corpus_list:
        raw_keywords_list.append(model.extract_keywords(docs=corpus, keyphrase_ngram_range=keyphrase_ngram_range,
                                                    stop_words=None, top_n=top_n, diversity=0.7))
    return raw_keywords_list

# Функция необходима для преобразования списка, получаемого после extract_keyphrases(), в словарь, пригодный для исопльзования в библиотеке wordcloud
def get_dict_keyphrases(keywords_lists, threshold=0.5) -> dict:
    '''Destined for wordcloud.
       Returns dictionary: key = keyword, value = [0,1]'''
    propper_keywords = {}
    for keyword_list in keywords_lists:
        for keyword in keyword_list:
            if keyword[1] >= threshold:
                propper_keywords[keyword[0]] = keyword[1]
    return propper_keywords

# Токенизация и очистка от стоп-слов (не используется, поскольку отсутствие стоп-слов портит семантику корпуса => несвязанные ключевые N-граммы)
def delete_stop_words(list_of_texts : list[str], language='russian', allowed_stopwords : list[str]=None):
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')
    stopwords = nltk.corpus.stopwords.words(language)

    list_of_tokens = []
    for text in list_of_texts:
        list_of_tokens.append(nltk.tokenize.word_tokenize(text, language=language))
    cleaned_corpus_list = []
    allowed_stopwords = allowed_stopwords
    for review_tokens in list_of_tokens:
        cleaned_corpus = []
        for token in review_tokens:
            if (token not in stopwords) or (token in allowed_stopwords):
                cleaned_corpus.append(token)
        cleaned_corpus_list.append(' '.join(cleaned_corpus))
    return cleaned_corpus_list