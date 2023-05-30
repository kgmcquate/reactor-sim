from django.urls import path

from . import views

urlpatterns = [
    path('', views.get_init, name='get_init'),
    path('solve/', views.solve, name='solve'),
    # path('button/', views.button, name='button')
]