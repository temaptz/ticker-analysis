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


class LocalLlmResponse:
    def __init__(self, prompt: str = None, response: str = None, model_name: str = None, pretrain_name: str = None):
        self.prompt = prompt
        self.response = response
        self.model_name = model_name
        self.pretrain_name = pretrain_name


class NewsRate2:
    sentiment: float or None = None
    impact_strength: float or None = None
    mention_focus: float or None = None
    model_name: str or None = None
    pretrain_name: str or None = None
    generation_time_sec: float or None = None
    generation_date: datetime.datetime or None = None
    llm_response: LocalLlmResponse or None = None
    influence_score: float or None = None

    def __init__(
            self,
            sentiment: float or None = None,
            impact_strength: float or None = None,
            mention_focus: float or None = None,
            model_name: str or None = None,
            pretrain_name: str or None = None,
            generation_time_sec: float or None = None,
            generation_date: datetime.datetime or None = None,
            llm_response: LocalLlmResponse or None = None,
    ):
        self.sentiment = sentiment
        self.impact_strength = impact_strength
        self.mention_focus = mention_focus
        self.model_name = model_name
        self.pretrain_name = pretrain_name
        self.generation_time_sec = generation_time_sec
        self.generation_date = generation_date
        self.llm_response = llm_response

    # Это отражает влияние одной новости на потенциальное изменение цены акции - позитивное или негативное
    def get_influence_score_value(self) -> float or None:
        if self.is_ready_to_calc():
            try:
                self.influence_score = self.sentiment * self.impact_strength * self.mention_focus
                return self.influence_score
            except Exception as e:
                print('ERROR NewsRate2 get_influence_score', e)
        return None

    def is_ready_to_calc(self) -> bool:
        return self.sentiment is not None and self.impact_strength is not None and self.mention_focus is not None


class NewsRatePeriod2:
    date_from: datetime.datetime = None
    date_to: datetime.datetime = None
    news_rate_list: [NewsRate2] = []

    def __init__(self, date_from: datetime.datetime = None, date_to: datetime.datetime = None, news_rate_list: [NewsRate2] = []):
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
                    if (score := i.get_influence_score_value()) is not None
                )

                return weekly_news_score / news_len

        except Exception as e:
            print('ERROR NewsRatePeriod2 get_total_avg_score', e)
        return None
