
from django.urls import path
from sc_app import views

app_name = 'sc_app'

urlpatterns = [
    path('data/', views.data, name='data'),
    path('paper/', views.paper, name='paper'),
    path('people/', views.people, name='people')
]
