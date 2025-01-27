import feedparser


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

        if parsed_feed and parsed_feed.entries:
            for i in parsed_feed.entries:
                uid = i['link']
                title = i['title']
                text = i['summary']
                date = i['published']

                result.append((uid, title, text, date, source_name))

    return result

