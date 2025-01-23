import os
import sys

from lib import forecasts_save
from lib import predictions_save

# import instruments
# import prices
# import statistic
# import prepare_data
# import learn

if sys.argv[1] == 'collect-forecasts':  # Прогнозы аналитиков
    # forecasts_save.show_saved_forecasts()
    forecasts_save.save_favorite_forecasts()

if sys.argv[1] == 'collect-predictions':  # Предсказание нейросети
    predictions_save.save_favorite_predictions()

# instruments.show_instruments()
# prices.show_prices()
# statistic.collect()
# prepare_data.show()
# prepare_data.prepare_cards()
# prepare_data.get_saved()
# learn.learn()
