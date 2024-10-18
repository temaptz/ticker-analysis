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
