from openpyxl.workbook import Workbook

wb = Workbook()
ws = wb.active

row = ('Hello', 'Boosted_d16')
ws.append(row)
wb.save('excelfile.xlsx')
