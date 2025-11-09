from django.urls import path
from . import views

urlpatterns = [
   
    path('', views.index, name='index'), 
    
   
    path('game/<slug:game_slug>/', views.game_dashboard, name='game_dashboard'),
    

    path('auth/<slug:game_slug>/', views.handle_auth, name='handle_auth'),
    
  
    path('post_lfg/', views.handle_lfg_post, name='handle_lfg_post'), 
    
  
    path('logout/', views.logout, name='logout'),
    
 
]