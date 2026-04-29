from django.urls import path
from .views import RouteAPIView, index

urlpatterns = [
    path('', index, name='index'),
    path('route/', RouteAPIView.as_view(), name='route-api'),
]
