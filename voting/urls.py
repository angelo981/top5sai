from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('campaign/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    path('campaign/<int:pk>/results/', views.voting_results, name='voting_results'),
    path('campaign/<int:campaign_id>/category/<int:category_id>/vote/', views.submit_vote, name='submit_vote'),
    path('campaign/<int:campaign_id>/category/<int:category_id>/results/', views.get_results, name='get_results'),
]
