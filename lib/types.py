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
