import datetime


class NewsDbRecord:
    def __init__(self, uid: str, title: str, text: str, date: datetime.datetime, source_name: str):
        self.uid = uid
        self.title = title
        self.text = text
        self.date = date
        self.source_name = source_name


class NewsRate:
    def __init__(self, positive_percent=0, negative_percent=0, neutral_percent=0):
        self.positive_percent = positive_percent
        self.negative_percent = negative_percent
        self.neutral_percent = neutral_percent


class NewsRateAbsoluteYandex:
    def __init__(self, positive_total=0, negative_total=0, neutral_total=0):
        self.positive_total = positive_total
        self.negative_total = negative_total
        self.neutral_total = neutral_total

class NewsRate2:
    sentiment = None  # эмоциональный/финансовый тон новости (от -1.0 до +1.0)
    impact_strength = None  # сила потенциального влияния на цену акций (0.0 - не повлияет, 1.0 - повлияет значительно)
    mention_focus = None  # Степень акцентированности упоминания компании (0.0 - вскользь, 1.0 - явно, подробно)

    def __int__(self, sentiment: float = None, impact_strength: float = None, mention_focus: float = None):
        self.sentiment = sentiment
        self.impact_strength = impact_strength
        self.mention_focus = mention_focus

    # Это отражает влияние одной новости на потенциальное изменение цены акции - позитивное или негативное
    def get_influence_score(self) -> float or None:
        if self.sentiment is not None and self.impact_strength is not None and self.mention_focus is not None:
            try:
                return self.sentiment * self.impact_strength * self.mention_focus
            except Exception as e:
                print('ERROR NewsRate2 get_influence_score', e)
        return None


class NewsRatePeriod2:
    date_from: datetime.datetime = None
    date_to: datetime.datetime = None
    news_rate_list: [NewsRate2] = []

    def __int__(self, date_from: datetime.datetime = None, date_to: datetime.datetime = None, news_rate_list: [NewsRate2] = []):
        self.date_from = date_from
        self.date_to = date_to
        self.news_rate_list = news_rate_list

    # Качество новостного фона независимо от количества новостей
    def get_total_avg_score(self) -> float or None:
        try:
            news_len = len(self.news_rate_list)
            if news_len > 0:
                # Общее "давление" новостного фона — положительное или отрицательное.
                weekly_news_score = sum(
                    score for i in self.news_rate_list
                    if (score := i.get_influence_score()) is not None
                )

                return weekly_news_score / news_len

        except Exception as e:
            print('ERROR NewsRatePeriod2 get_total_avg_score', e)
        return None
