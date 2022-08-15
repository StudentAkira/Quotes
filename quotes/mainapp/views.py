import requests
from django.core.cache import cache
from django.shortcuts import render
from rest_framework.views import APIView
import xmltodict


class MainPageAPIView(APIView):
    def get(self, request):
        if cache.get('quote_names'):
            quote_names = cache.get('quote_names')
            return render(request, 'main.html', {'quote_names': quote_names})

        quote_names = []
        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')

        data = xmltodict.parse(response.text)
        for item in data['ValCurs']['Valute']:
            quote_names += [item['CharCode']]
        cache.set('quote_names', quote_names)
        return render(request, 'main.html', {'quote_names': quote_names})


class TablePageView(APIView):
    def post(self, request):
        currencies = list(request.data)[1:]
        if cache.get('quoted_currencies'):
            filtered_data = list(filter(lambda x: x['CharCode'] in currencies, cache.get('quoted_currencies')))
            if len(filtered_data) == len(currencies):
                return render(request, 'table.html', {'data': filtered_data})

        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')
        data = xmltodict.parse(response.text)
        filtered_data = list(filter(lambda x: x['CharCode'] in currencies, data['ValCurs']['Valute']))
        cache.set('quoted_currencies', filtered_data)
        return render(request, 'table.html', {'data': filtered_data})
