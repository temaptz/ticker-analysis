from django.urls import path
from . import views

# router = routers.DefaultRouter()
# router.register(r'favorites', views.HeroViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('instruments', views.instruments_list),
    path('instrument', views.instrument_info),
    path('instrument/last_price', views.instrument_last_price),
    path('instrument/price_by_date', views.instrument_price_by_date),
    path('instrument/history_prices', views.instrument_history_prices),
    path('instrument/forecasts', views.instrument_forecasts),
    path('instrument/history_forecasts', views.instrument_history_forecasts),
    path('instrument/history_forecasts/graph', views.instrument_history_forecasts_graph),
    path('instrument/fundamentals', views.instrument_fundamentals),
    path('instrument/fundamentals/history', views.instrument_fundamentals_history),
    path('instrument/prediction/graph', views.instrument_prediction_graph),
    path('instrument/prediction/history_graph', views.instrument_prediction_history_graph),
    path('instrument/prediction', views.instrument_prediction),
    path('instrument/balance', views.instrument_balance),
    path('instrument/operations', views.instrument_operations),
    path('instrument/news/list_rated', views.instrument_news_list_rated),
    path('instrument/brand', views.instrument_brand),
    path('instrument/invest_calc', views.instrument_invest_calc),
    path('instrument/tech_analysis/graph', views.tech_analysis_graph),
    path('instrument/recommendation', views.instrument_recommendation),
    path('gpt', views.gpt),
]
