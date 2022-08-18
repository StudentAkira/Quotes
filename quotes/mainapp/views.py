import io
import json
import os
from io import BytesIO

import requests
from django.core.cache import cache
import tempfile
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl.workbook import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework.views import APIView
import xmltodict
from fpdf import FPDF

from quotes.settings import BASE_DIR


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


class ExportResultsAPIView(APIView):
    def get(self, request):
        data = dict(request.query_params)['data'][0].strip('[]')[1:-1:].split('}, {')
        amount_of_rows = len(dict(request.query_params)['data'][0].strip('[]')[1:-1:].split('}, {'))

        if request.query_params['datatype'] == 'xlsx':
            wb = Workbook()
            ws = wb.active
            ws.append(list(json.loads('{' + data[0].replace("'", '"') + '}').keys()))
            for row in range(amount_of_rows):
                new_row = json.loads('{'+data[row].replace("'", '"')+'}')
                print(list(new_row.values()))
                ws.append(list(new_row.values()))
            with BytesIO(save_virtual_workbook(wb)) as file:
                response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="foo.xlsx"'
                return response
        if request.query_params['datatype'] == 'pdf':
            data = [
                list(json.loads('{' + data[0].replace("'", '"') + '}').keys(), ),
            ]+[list(json.loads('{' + data[i].replace("'", '"') + '}').values()) for i in range(len(data))]
            print(data)
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('gargi', '', os.path.join(BASE_DIR, 'media\gargi.ttf'), uni=True)
            pdf.set_font('gargi', '', 14)
            line_height = pdf.font_size * 5
            col_width = pdf.epw / 6 # distribute content evenly
            for row in data:
                for datum in row:
                    pdf.multi_cell(col_width, line_height, datum, border=1,
                                   new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
                pdf.ln(line_height)
            with io.BytesIO(pdf.output(dest='S')) as file:
                response = HttpResponse(file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="foo.pdf"'
                return response
        return HttpResponse('h1')


