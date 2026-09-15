from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('service/', views.service, name='service'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('blogs/', views.blogs, name='blogs'),
    path('partners/', views.partners, name='partners'),
    path('contact/', views.contact, name='contact'),
    path('api/submit-message/', views.submit_message, name='submit_message'),
]
