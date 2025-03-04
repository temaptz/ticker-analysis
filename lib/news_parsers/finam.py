import feedparser
from lib import date_utils, utils


def get_news():
    source_name = 'FINAM'
    source_links = [
        'https://www.finam.ru/analysis/conews/rsspoint/',  # Новости компаний
        'https://www.finam.ru/international/advanced/rsspoint/',  # Новости развитых рынков
        'https://www.finam.ru/analysis/forecasts/rsspoint/',  # Макроэкономические сценарии и прогнозы
        'https://www.finam.ru/analysis/nslent/rsspoint/',  # Рынок и Аналитика Лента комментариев
        'https://www.finam.ru/analytics/rsspoint/',  # Обзоры и идеи
    ]
    result = list()

    for source_link in source_links:
        print(source_link)

        parsed_feed = feedparser.parse(source_link)

        if parsed_feed and parsed_feed.entries:
            for i in parsed_feed.entries:
                try:
                    uid = utils.get_md5(i['link'])
                    title = i['title']
                    text = i['summary']
                    date = date_utils.parse_date(i['published'])

                    result.append((uid, title, text, date, source_name))

                except Exception as e:
                    print(f'ERROR PARSING NEWS FROM {source_name}: ', e)

    return result

