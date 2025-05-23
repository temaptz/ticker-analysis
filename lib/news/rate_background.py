import time
import datetime
from lib import date_utils, instruments, yandex, news, db_2, types, utils

def rate_all_news() -> None:
    for date in date_utils.get_dates_interval_list(
            date_from=datetime.datetime.now() - datetime.timedelta(days=30),
            date_to=datetime.datetime.now(),
    ):
        for instrument in instruments.get_instruments_white_list():
            subject_name = yandex.get_human_name(legal_name=instrument.name)
            date_from = datetime.datetime.combine(date=date, time=datetime.time(hour=0, minute=0, second=0, microsecond=0))
            date_to = datetime.datetime.combine(date=date, time=datetime.time(hour=23, minute=59, second=59, microsecond=999999))

            news_list = news.news.get_news_by_instrument_uid(
                instrument_uid=instrument.uid,
                start_date=date_from,
                end_date=date_to,
            ) or []

            print(f'WILL RATE NEWS - {subject_name} [{instrument.ticker}] ({date_from} - {date_to}) NEWS COUNT: {len(news_list)}')

            for n in news_list:
                print('---------------------------------NEWS RATED START---------------------------------')
                print(f'NEWS TEXT: {utils.clean_news_text_for_llm(title=n.title, text=n.text)}]')

                start = time.time()
                rate: types.NewsRate2 = news.news_rate_v2.get_news_rate(
                    news_uid=[n.news_uid],
                    subject_name=subject_name,
                )
                end = time.time()
                generation_time_sec = float(f'{end - start:.4f}')

                if rate:
                    db_2.news_rate_2_db.insert_or_update_rate(
                        instrument_uid=instrument.uid,
                        news_uid=n.news_uid,
                        news_rate=rate,
                        model_name=rate.llm_response.model_name,
                        pretrain_name=rate.llm_response.pretrain_name,
                        generation_time_sec=generation_time_sec,
                    )
                    print(f'NEWS RATE: [sentiment: {rate.sentiment}; impact_strength: {rate.impact_strength}; mention_focus: {rate.mention_focus}]')
                    print(f'NEWS TOTAL RATE: {rate.get_influence_score_value()}')

                else:
                    print('[NEWS NOT RATED]', rate)

                print(f'GENERATION TIME: {generation_time_sec} sec')
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^NEWS RATED END^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

                time.sleep(60)
