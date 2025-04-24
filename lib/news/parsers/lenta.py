import feedparser
import ssl
from lib import date_utils, utils


def get_news():
    source_name = 'LENTA'
    source_links = [
        'https://lenta.ru/rss/news',
    ]
    result = list()

    for source_link in source_links:
        print(source_link)

        ssl._create_default_https_context = ssl._create_unverified_context

        parsed_feed = feedparser.parse(source_link)

        if parsed_feed and parsed_feed.entries:
            for i in parsed_feed.entries:
                try:
                    uid = utils.get_md5(i['id'])
                    title = i['title']
                    text = i['summary']
                    date = date_utils.parse_date(i['published'])

                    result.append((uid, title, text, date, source_name))

                except Exception as e:
                    print(f'ERROR PARSING NEWS FROM {source_name}: ', e)

    return result

