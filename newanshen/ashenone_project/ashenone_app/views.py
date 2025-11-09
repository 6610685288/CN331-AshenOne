from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import GAMES_LIST, LFGPost, CustomUser # Import ORM Models

# --- 1. Game Selection & Main Dashboard (Guest/User) ---

def index(request):
  
    context = {
        'GAMES_LIST': GAMES_LIST 
    }
    return render(request, 'ashenone_app/game_selection.html', context)

def game_dashboard(request, game_slug):
 
    game_info = next((g for g in GAMES_LIST if g['slug'] == game_slug), None)
    if not game_info:
        return redirect('index')

    current_game_name = game_info['name']
    
 
    posts = LFGPost.objects.filter(game_name=current_game_name).order_by('-created_at')
    
  
    view_type = request.GET.get('view', 'login')
    
    context = {
        'current_game_name': current_game_name,
        'game_slug': game_slug,
        'user': request.user, 
        'posts': posts,
        'view_type': view_type,
        'is_login': view_type == 'login'
    }
    
    return render(request, 'ashenone_app/game_dashboard.html', context)

# --- 2. Authentication (US-U1) ---

def handle_auth(request, game_slug):
  
    if request.method != 'POST':
        return redirect('game_dashboard', game_slug=game_slug)

    action = request.POST.get('action')
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if action == 'register':
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, "รหัสผ่านไม่ตรงกัน โปรดตรวจสอบอีกครั้ง")
            return redirect(f"{reverse('game_dashboard', args=[game_slug])}?view=register")
            
        try:
           
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' ถูกใช้แล้ว")
                return redirect(f"{reverse('game_dashboard', args=[game_slug])}?view=register")
          
            new_user = CustomUser.objects.create_user(
                username=username, 
                password=password
            )
            
            login(request, new_user)
            messages.success(request, f"ลงทะเบียนสำเร็จ! ยินดีต้อนรับ, {username}")

        except Exception as e:
            messages.error(request, f"ลงทะเบียนล้มเหลว: {e}")
            return redirect(f"{reverse('game_dashboard', args=[game_slug])}?view=register")

    elif action == 'login':
       
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
        
            if user.suspended:
                messages.error(request, "บัญชีของคุณถูกระงับการใช้งาน")
                return redirect(f"{reverse('game_dashboard', args=[game_slug])}?view=login")
                
            login(request, user)
            messages.success(request, f"ล็อกอินสำเร็จ! ยินดีต้อนรับกลับ, {username}")
        else:
            messages.error(request, "เข้าสู่ระบบล้มเหลว: Username หรือ Password ไม่ถูกต้อง")
            return redirect(f"{reverse('game_dashboard', args=[game_slug])}?view=login")

    return redirect('game_dashboard', game_slug=game_slug)

def logout(request):
    """
    View 4: จัดการการ Logout (ใช้ Django Auth)
    """
    auth_logout(request)
    messages.success(request, "คุณออกจากระบบเรียบร้อยแล้ว")
    return redirect('index')

# --- 3. LFG Post Management (US-U2) ---

@login_required(login_url='/') 
def handle_lfg_post(request):
   
    if request.method != 'POST':
        return redirect('index')
    
    game_name = request.POST.get('gameName')
    game_slug = next((g['slug'] for g in GAMES_LIST if g['name'] == game_name), 'index')

    post_data = {
        'gameName': game_name,
        'platform': request.POST.get('platform'),
        'bossName': request.POST.get('bossName'),
        'description': request.POST.get('description')
    }

    if not post_data['bossName'] or not post_data['description']:
        messages.error(request, "กรุณากรอกชื่อบอสและรายละเอียดให้ครบถ้วน!")
    else:
      
        LFGPost.objects.create(
            user=request.user, 
            game_name=post_data['gameName'],
            platform=post_data['platform'],
            boss_name=post_data['bossName'],
            description=post_data['description'],
            status='Active'
        )
        messages.success(request, "สร้างโพสต์ LFG สำเร็จ!")
    
    return redirect('game_dashboard', game_slug=game_slug)