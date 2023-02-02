import io
import json
import os
from io import BytesIO
import requests
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from openpyxl.workbook import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework.views import APIView
import xmltodict
from fpdf import FPDF

from quotes.settings import BASE_DIR


class MainPageAPIView(View):
    def get(self, request):
        if cache.get('quote_names'):
            quote_names = cache.get('quote_names')
            response = render(request, 'main.html', {'quote_names': quote_names})
            return response

        quote_names = []
        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')

        data = xmltodict.parse(response.text)
        for item in data['ValCurs']['Valute']:
            quote_names += [item['CharCode']]
        data_in_cache = cache.get('quoted_names')
        new_data_in_cache = list(set(data_in_cache + quote_names) if data_in_cache else quote_names)
        cache.set('quote_names', new_data_in_cache)
        response = render(request, 'main.html', {'quote_names': quote_names})
        return response


class TablePageView(View):

    def get(self, request):
        currencies = list(request.GET)[1:]
        if cache.get('quoted_currencies'):
            filtered_data = list(filter(lambda x: x['CharCode'] in currencies, cache.get('quoted_currencies')))
            if len(filtered_data) == len(currencies):
                response = render(request, 'table.html', {'data': filtered_data, 'currencies': currencies})
                print('all data from cache')
                return response

        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')
        data = xmltodict.parse(response.text)
        filtered_data = list(filter(lambda x: x['CharCode'] in currencies, data['ValCurs']['Valute']))
        data_in_cache = cache.get('quoted_currencies')

        new_data = list(filter(lambda item: item not in data_in_cache, filtered_data))\
            if data_in_cache else filtered_data

        cache.set('quoted_currencies', data_in_cache+new_data) \
            if data_in_cache else cache.set('quoted_currencies', filtered_data)

        response = render(request, 'table.html', {'data': filtered_data, 'currencies': currencies})
        print('data from request. cant get such items from cache : ', new_data)
        return response


class ExportResultsAPIView(View):
    def get(self, request):
        print(request.GET)
        currencies = dict(request.GET)['currencies'][0][1:-1].replace("'", '').split(', ')

        if cache.get('quoted_currencies'):
            data = list(filter(lambda item: item['CharCode'] in currencies, cache.get('quoted_currencies')))
        else:
            response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')
            data = xmltodict.parse(response.text)
            data = list(filter(lambda x: x['CharCode'] in currencies, data['ValCurs']['Valute']))
        data_type = dict(request.GET)['datatype'][0]
        
        amount_of_rows = len(data)
        print('\n\n ', data, ' \n\n')
        print('\n\n ', data_type, ' \n\n')
        print('\n\n ', amount_of_rows, ' \n\n')

        if data_type == 'xlsx':
            wb = Workbook()
            ws = wb.active
            ws.append(list(data[0].keys()))
            for row in range(amount_of_rows):
                new_row = data[row]
                print(new_row['Name'], '------------------------------==============')
                ws.append(list(new_row.values()))
            with BytesIO(save_virtual_workbook(wb)) as file:
                response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="foo.xlsx"'
                return response

        if data_type == 'pdf':
            data = [list(data[0].keys())]+[list(data[i].values()) for i in range(len(data))]
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('fontF', '', os.path.join(BASE_DIR, 'media\\fontF.ttf'), uni=True)
            pdf.set_font('fontF', '', 14)
            line_height = pdf.font_size * 5
            col_width = pdf.epw / 6
            for row in data:
                for datum in row:
                    pdf.multi_cell(col_width, line_height, datum, border=1,
                                   new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
                pdf.ln(line_height)
            with BytesIO(pdf.output(dest='S')) as file:
                response = HttpResponse(file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="foo.pdf"'
                return response

        return HttpResponse('test')
