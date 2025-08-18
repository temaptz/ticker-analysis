# import datetime
# import os
from dotenv import load_dotenv

from lib import (
    telegram,
    docker,
    schedule,
    # users,
    # serializer,
    # news,
    # fundamentals_save,
    # predictions,
    # predictions_save,
    # utils,
    # date_utils,
    # yandex_disk,
    # agent,
    # invest_calc,
    # learn,
    schedule_llm,
)
from lib.db_2 import init, db_utils, predictions_db
# from lib.learn import model
# import pandas

load_dotenv()

init.init_db()
db_utils.optimize_db()

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule_llm.start_available_job()
    schedule.start_schedule()
else:
    print('NOT DOCKER')

    # schedule_llm.test_run()

    # learn.consensus.learn()

    # agent.get_invest_recommendation()
    # agent.instrument_rank_buy.update_recommendations()
    # agent.news_rank.rank_last_news()

    # news_500 =pandas.read_csv('./local_llm/news_500.csv')
    #
    # prompts = []
    # responses = []
    #
    # for n in news_500.itertuples():
    #     # print(n.subject_name)
    #     # print(n.news_text)
    #     # print(n.sentiment)
    #     # print(n.impact_strength)
    #     # print(n.mention_focus)
    #
    #     prompt = news.news_rate_v2.get_prompt(
    #         news_text=n.news_text,
    #         subject_name=n.subject_name,
    #     )
    #
    #     response = news.news_rate_v2.get_response(
    #         sentiment=n.sentiment,
    #         impact_strength=n.impact_strength,
    #         mention_focus=n.mention_focus
    #     )
    #
    #     prompts.append(prompt)
    #     responses.append(response)
    #
    # df = pandas.DataFrame({
    #     'prompt': prompts,
    #     'response': responses
    # })
    #
    # df.to_csv('./local_llm/dataset.csv', index=False)





    # schedule.start_schedule(







    # news.news_save.save_news()

    # for i in instruments.get_instruments_white_list():
    #     print(tech_analysis.get_tech_analysis(
    #         instrument_uid=i.uid,
    #         indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
    #         date_from=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7),
    #         date_to=datetime.datetime.now(datetime.timezone.utc),
    #     ))

    # ta_2.generate_data()
    # ta_2.learn()

    # invest_calc.get_report()

    # ta_1_2.prepare_data()
    # ta_1_2.learn()

    # db_2.migrate_sqlite.drop_tables()
    # init.init_db()
    # db_2.migrate_sqlite.copy_data_from_sqlite()
    # yandex_disk.upload_db_backup()
    # cache.clean()



    # predictions_save.save_predictions_ta_1_1()
    # ta_1_1.learn()
    # prepare_data.prepare_cards()
    # print(docker.is_prod())
    # print(docker.get_df())
    # news_db.replace_md5()
    # ta_2.generate_data()
    # predictions_save.save_predictions()
    # news = news_db.get_news_by_date_keywords_fts(
    #     start_date=utils.parse_json_date('2025-02-14'),
    #     end_date=utils.parse_json_date('2025-02-21'),
    #     keywords=['распадская', 'распадущенская']
    # )
    #
    # print('GOT NEWS', len(news))
    # news_save.save_news()

    # yandex_disk.upload_db_backup()

