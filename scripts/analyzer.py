from keybert import KeyBERT

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