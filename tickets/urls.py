from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('first/', views.first_event_redirect, name='first_event'),
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),
    path('spinny-demo/', views.spinny_demo, name='spinny_demo'),
    path('reserve/', views.reserve_tickets, name='reserve_tickets'),
    path('payment/<int:purchase_id>/', views.payment_transaction, name='payment_transaction'),
    path('ticket/<uuid:code>/download/', views.download_ticket, name='download_ticket'),
    path('purchase/', views.purchase_ticket, name='purchase_ticket'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('validate/', views.validate_ticket, name='validate_ticket'),
]
