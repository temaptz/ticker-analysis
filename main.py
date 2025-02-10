from lib import (
    telegram,
    docker,
    schedule,
    users,
    serializer,
    news
)

# import instruments
# import prices
# import statistic
# import prepare_data
# import learn


if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule.start_schedule()
else:
    print('ELSE')
    # news.get_news_by_instrument_uid()


# instruments.show_instruments()
# prices.show_prices()
# statistic.collect()
# prepare_data.show()
# prepare_data.prepare_cards()
# prepare_data.get_saved()
# learn.learn()
