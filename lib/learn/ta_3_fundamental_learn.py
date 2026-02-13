from datetime import datetime, timedelta, timezone

from lib import instruments, learn, date_utils
from lib.learn.ta_3_fundamental import Ta3FundamentalAnalysisCard


def generate_data():
    fundamental_beginning_date = datetime(year=2025, month=2, day=17, tzinfo=timezone.utc)
    date_start = date_utils.get_day_prediction_time(date=(fundamental_beginning_date + timedelta(days=learn.ta_3_fundamental.REPORT_DURATION_DAYS)))
    date_end = date_utils.get_day_prediction_time(date=datetime.now(timezone.utc) - timedelta(days=250)) # Надо learn.ta_3_fundamental.MAX_DAYS
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []
    records_keys = []

    print(f'GENERATE DATA {learn.model.TA_3_fundamental}')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end, is_skip_holidays=True):
            print('DATE', date)

            card = Ta3FundamentalAnalysisCard(
                instrument=instrument,
                date=date,
                fill_empty=True
            )

            print('CARD CSV')
            print(card.get_csv_record())

            return
