from django.urls import path
from . import views

urlpatterns = [
   
    path('', views.index, name='index'), 
    
   
    path('game/<slug:game_slug>/', views.game_dashboard, name='game_dashboard'),
    

    path('auth/<slug:game_slug>/', views.handle_auth, name='handle_auth'),
    
  
    path('post_lfg/', views.handle_lfg_post, name='handle_lfg_post'), 


    path('offer_help/<uuid:post_id>/', views.offer_help, name='offer_help'),


    path('content/<slug:game_slug>/<slug:content_slug>/', views.content_detail, name='content_detail'),


    path('chats/', views.chat_list_view, name='chat_list'),


    path('chat/<uuid:post_id>/', views.chat_room_view, name='chat_room'),


    path('api/chat/fetch/<uuid:post_id>/', views.fetch_messages_api, name='fetch_messages_api'),


    path('api/chat/send/<uuid:post_id>/', views.send_message_api, name='send_message_api'),
    
  
    path('logout/', views.logout, name='logout'),
]