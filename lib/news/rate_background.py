import time
import datetime
from lib import date_utils, instruments, yandex, news, db_2, types_util, utils

def run_rate_cycle(max_iterations_count: int = None) -> None:
    for date in date_utils.get_dates_interval_list(
        date_from=datetime.datetime(year=2025, month=2, day=1),
        date_to=datetime.datetime.now(),
        is_order_descending=True,
    ):
        iterations_counter = 0

        for instrument in instruments.get_instruments_white_list():
            subject_name = instruments.get_instrument_human_name(uid=instrument.uid)
            date_from = datetime.datetime.combine(date=date, time=datetime.time(hour=0, minute=0, second=0, microsecond=0))
            date_to = datetime.datetime.combine(date=date, time=datetime.time(hour=23, minute=59, second=59, microsecond=999999))

            news_list = news.news.get_news_by_instrument_uid(
                instrument_uid=instrument.uid,
                start_date=date_from,
                end_date=date_to,
            ) or []

            print(f'WILL RATE NEWS - {subject_name} [{instrument.ticker}] ({date_from} - {date_to}) NEWS COUNT: {len(news_list)}')

            for n in news_list:
                if r := db_2.news_rate_2_db.get_rate(instrument_uid=instrument.uid, news_uid=n.news_uid):
                    print('[NEWS ALREADY RATED]', r[0] if r and len(r) > 0 else r)
                else:
                    print('---------------------------------NEWS RATED START---------------------------------')
                    print(f'NEWS TEXT: {utils.clean_news_text_for_llm(title=n.title, text=n.text)}]')

                    start = time.time()
                    rate: types_util.NewsRate2 = news.news_rate_v2.get_news_rate(
                        news_uid=n.news_uid,
                        instrument_uid=instrument.uid,
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

                        if max_iterations_count and iterations_counter >= max_iterations_count:
                            return

                        iterations_counter += 1

                    else:
                        print('[NEWS NOT RATED]', rate)

                    print(f'GENERATION TIME: {generation_time_sec} sec')
                    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^NEWS RATED END^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

                    time.sleep(60)
