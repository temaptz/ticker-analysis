from django.urls import path
from . import views

# router = routers.DefaultRouter()
# router.register(r'favorites', views.HeroViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('instruments', views.instruments_list),
    path('instrument', views.instrument_info),
    path('instrument/last_prices', views.instrument_last_prices),
    path('instrument/price_by_date', views.instrument_price_by_date),
    path('instrument/history_prices', views.instrument_history_prices),
    path('instrument/consensus_forecast', views.instrument_consensus_forecast),
    path('instrument/history_forecasts', views.instrument_history_forecasts),
    path('instrument/fundamental', views.instrument_fundamental),
    path('instrument/prediction/graph', views.instrument_prediction_graph),
    path('instrument/prediction', views.instrument_prediction),
    path('instrument/balance', views.instrument_balance),
    path('instrument/operations', views.instrument_operations),
    path('instrument/news', views.instrument_news),
    path('instrument/brand', views.instrument_brand),
]
