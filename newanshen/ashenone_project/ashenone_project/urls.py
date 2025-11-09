from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    # --- เปิด Admin "ตามปกติ" ของ Django ---
    path('admin/', admin.site.urls), 
    # ------------------------------------
    
    # --- รวม URLS จาก App ---
    path('', include('ashenone_app.urls')), 
    # ---------------------------------
]