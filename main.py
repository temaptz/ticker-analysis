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
    news.get_sorted_news_by_instrument_uid_by_source('35fb8d6b-ed5f-45ca-b383-c4e3752c9a8a')


# instruments.show_instruments()
# prices.show_prices()
# statistic.collect()
# prepare_data.show()
# prepare_data.prepare_cards()
# prepare_data.get_saved()
# learn.learn()
