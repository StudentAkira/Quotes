from django.contrib import admin
from django.urls import path, re_path
from mainapp.views import MainPageAPIView, TablePageView, ExportResultsAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', MainPageAPIView.as_view()),
    path('table/', TablePageView.as_view()),
    path('export/', ExportResultsAPIView.as_view()),
]
