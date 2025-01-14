import os
import sys

lib_directory = os.path.abspath('./lib')
db_directory = os.path.abspath('./lib/db')
invest_lib_directory = os.path.abspath('./apiserver/rest/invest')
sys.path.append(lib_directory)
sys.path.append(db_directory)
sys.path.append(invest_lib_directory)

# import instruments
# import prices
# import statistic
import forecasts_save
import predictions_save
# import prepare_data
# import learn

# instruments.show_instruments()
# prices.show_prices()
# statistic.collect()
# forecasts_save.save_favorite_forecasts()  # Прогнозы аналитиков
predictions_save.save_favorite_predictions()  # Предсказание нейросети
# forecasts_save.show_saved_forecasts()
# prepare_data.show()
# prepare_data.prepare_cards()
# prepare_data.get_saved()
# learn.learn()
