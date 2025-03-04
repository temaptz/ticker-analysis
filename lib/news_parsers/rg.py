import feedparser
from lib import date_utils, utils


def get_news():
    source_name = 'RG'
    source_links = [
        'https://rg.ru/xml/index.xml',  # Главное
        'https://rg.ru/xml/rubrics/ekonomika.xml',  # Экономика
    ]
    result = list()

    for source_link in source_links:
        print(source_link)

        parsed_feed = feedparser.parse(source_link)

        print(parsed_feed)

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

