import feedparser


def get_news():
    source_name = 'RBC'
    source_links = [
        'https://rssexport.rbc.ru/rbcnews/news/90/full.rss',  # Главное
    ]
    result = list()

    for source_link in source_links:
        print(source_link)

        parsed_feed = feedparser.parse(source_link)

        if parsed_feed and parsed_feed.entries:
            for i in parsed_feed.entries:
                uid = i['rbc_news_news_id']
                title = i['title']
                text = i['rbc_news_full-text']
                date = i['published']

                result.append((uid, title, text, date, source_name))

    return result

