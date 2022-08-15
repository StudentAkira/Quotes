from django.contrib import admin
from django.urls import path
from mainapp.views import MainPageAPIView, TablePageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', MainPageAPIView.as_view()),
    path('table/', TablePageView.as_view()),
]
