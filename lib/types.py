import datetime


class NewsDbRecord:
    def __init__(self, uid: str, title: str, text: str, date: datetime.datetime, source_name: str):
        self.uid = uid
        self.title = title
        self.text = text
        self.date = date
        self.source_name = source_name
