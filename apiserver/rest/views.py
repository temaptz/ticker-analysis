from rest_framework.decorators import api_view
from django.http import HttpResponse
from .invest import instruments
from .invest import serializer
import json


@api_view(['GET'])
def instruments_list(request):
    resp = list()

    for i in instruments.get_favorites():
        resp.append(serializer.getDictByObject(i))

    return HttpResponse(json.dumps(resp))

@api_view(['GET'])
def instrument_info(request):
    resp = ''
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

        if instrument:
            resp = serializer.getDictByObject(instrument)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_last_prices(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        for i in instruments.get_instrument_last_price_by_uid(uid):
            resp.append(serializer.getDictByObject(i))

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_history_prices(request):
    resp = ''
    uid = request.GET.get('uid')

    if uid:
        price = instruments.get_instrument_history_price_by_uid(uid)

        if price:
            resp = serializer.getDictByObject(price)

    return HttpResponse(json.dumps(resp))
