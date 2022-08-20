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
        cache.set('quote_names', quote_names)

        response = render(request, 'main.html', {'quote_names': quote_names})
        return response


class TablePageView(View):
    def post(self, request):
        currencies = list(request.POST)[1:]
        if cache.get('quoted_currencies'):
            filtered_data = list(filter(lambda x: x['CharCode'] in currencies, cache.get('quoted_currencies')))
            if len(filtered_data) == len(currencies):
                response = render(request, 'table.html', {'data': filtered_data})
                return response

        response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=14/08/2022')
        data = xmltodict.parse(response.text)
        filtered_data = list(filter(lambda x: x['CharCode'] in currencies, data['ValCurs']['Valute']))
        cache.set('quoted_currencies', filtered_data)
        response = render(request, 'table.html', {'data': filtered_data})
        return response


class ExportResultsAPIView(View):
    def get(self, request):
        data = dict(request.GET)['data'][0].strip('[]')[1:-1:].split('}, {')
        amount_of_rows = len(dict(request.GET)['data'][0].strip('[]')[1:-1:].split('}, {'))

        if request.GET['datatype'] == 'xlsx':
            wb = Workbook()
            ws = wb.active
            ws.append(list(json.loads('{' + data[0].replace("'", '"') + '}').keys()))
            for row in range(amount_of_rows):
                new_row = json.loads('{'+data[row].replace("'", '"')+'}')
                ws.append(list(new_row.values()))
            with BytesIO(save_virtual_workbook(wb)) as file:
                response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="foo.xlsx"'
                return response

        if request.GET['datatype'] == 'pdf':
            data = [
                list(json.loads('{' + data[0].replace("'", '"') + '}').keys(), ),
            ]+[list(json.loads('{' + data[i].replace("'", '"') + '}').values()) for i in range(len(data))]
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('gargi', '', os.path.join(BASE_DIR, 'media\gargi.ttf'), uni=True)
            pdf.set_font('gargi', '', 14)
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

