from wordcloud import WordCloud
from config import Config

class WordCloudGenerator:
    def __init__(self, config: Config):
        self.config = config

    @classmethod
    def generate(cls, freq_dict: dict[str, float], filepath=None, save_image=True):
        wc = WordCloud(
            width=Config.WORDCLOUD_WIDTH,
            height=Config.WORDCLOUD_HEIGHT,
            background_color=Config.WORDCLOUD_BACKGROUND_COLOR,
            colormap=Config.WORDCLOUD_COLORMAP,
            collocations=Config.WORDCLOUD_COLLOCATIONS,
            random_state=Config.WORDCLOUD_RANDOM_STATE,
        )
        wc.generate_from_frequencies(freq_dict)
        image = wc.to_image()
        if save_image:
            image.save(filepath)
        return image

