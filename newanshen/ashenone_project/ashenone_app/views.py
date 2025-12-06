from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import GAMES_LIST, LFGPost, CustomUser, Offer, ChatMessage, GuideContent, Report
import logging
import json
from django.db.models import Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)

# --- 1. Game Selection & Main Dashboard (Guest/User) ---

def index(request):
  
    context = {
        'GAMES_LIST': GAMES_LIST 
    }
    return render(request, 'ashenone_app/game_selection.html', context)

def game_dashboard(request, game_slug):

    game_info = next((g for g in GAMES_LIST if g['slug'] == game_slug), None)
    if not game_info:
        messages.error(request, "Game not found.")
        return redirect('index')

    current_game_name = game_info['name']

    posts_qs = LFGPost.objects.filter(
        game_name=current_game_name
    ).exclude(status='Completed').order_by('-created_at')
    
    # --- LFG POSTS LOGIC ---
    posts_qs = LFGPost.objects.filter(game_name=current_game_name).order_by('-created_at')
    
    if request.user.is_authenticated:
        user_offers = Offer.objects.filter(offered_by=request.user)
        posts_qs = posts_qs.prefetch_related(
            Prefetch('offers', queryset=user_offers, to_attr='current_user_offers')
        )
    
    posts_page_num = request.GET.get('posts_page', 1) 
    posts_paginator = Paginator(posts_qs, 5) 
    try:
        posts = posts_paginator.page(posts_page_num)
    except PageNotAnInteger:
        posts = posts_paginator.page(1)
    except EmptyPage:
        posts = posts_paginator.page(posts_paginator.num_pages)


    # --- CONTENT LIST LOGIC ---
    content_list_qs = GuideContent.objects.filter(game_name=current_game_name).order_by('category', 'title')

    content_page_num = request.GET.get('content_page', 1) 
    content_paginator = Paginator(content_list_qs, 5) 
    try:
        content_list = content_paginator.page(content_page_num)
    except PageNotAnInteger:
        content_list = content_paginator.page(1)
    except EmptyPage:
        content_list = content_paginator.page(content_paginator.num_pages)
    
    
    view_type = request.GET.get('view', 'login')
    
    context = {
        'current_game_name': current_game_name,
        'game_slug': game_slug,
        'user': request.user, 
        'posts': posts, 
        'content_list': content_list, 
        'view_type': view_type,
        'is_login': view_type == 'login'
    }
    
    return render(request, 'ashenone_app/game_dashboard.html', context)

# --- 2. Authentication ---

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
    auth_logout(request)
    messages.success(request, "คุณออกจากระบบเรียบร้อยแล้ว")
    return redirect('index')

# --- 3. LFG Post Management ---

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

@login_required(login_url='/')
def offer_help(request, post_id):
    if request.method != 'POST':
        return redirect('index')

    post = get_object_or_404(LFGPost, id=post_id) 
    game_slug = next((g['slug'] for g in GAMES_LIST if g['name'] == post.game_name), 'index')
    
    if post.user == request.user:
        messages.error(request, "ไม่สามารถเสนอช่วยเหลือโพสต์ที่คุณสร้างเองได้")
        return redirect('game_dashboard', game_slug=game_slug)
        
    existing_offer = Offer.objects.filter(post=post, offered_by=request.user).first()

    if existing_offer:
        messages.info(request, f"คุณได้เสนอความช่วยเหลือโพสต์นี้ไปแล้ว (เข้าสู่ห้องแชท: {post.boss_name})")
        return redirect('chat_room', post_id=post.id) 
        
    try:
        Offer.objects.create(
            post=post,
            offered_by=request.user,
            message=f"{request.user.username} offers assistance for {post.boss_name}"
        )

        if post.status == 'Active':
            post.status = 'In Progress'
            post.save() 
            messages.success(request, f"เสนอความช่วยเหลือสำเร็จ! สถานะโพสต์: In Progress. เริ่มแชทได้เลย: {post.boss_name}")
        else:
            messages.info(request, f"เสนอความช่วยเหลือสำเร็จ! โพสต์นี้กำลังดำเนินการอยู่. เข้าห้องแชท: {post.boss_name}")
        
    except Exception as e:
        messages.error(request, "เกิดข้อผิดพลาดในการบันทึกการเสนอช่วยเหลือ")
        logger.error(f"Error creating offer: {e}")
        return redirect('game_dashboard', game_slug=game_slug)
    
    return redirect('chat_room', post_id=post.id)

@login_required(login_url='/')
def chat_room_view(request, post_id):
    post = get_object_or_404(LFGPost, id=post_id) 
    
    is_owner = post.user == request.user
    has_offered = Offer.objects.filter(post=post, offered_by=request.user).exists()
    
    if not is_owner and not has_offered:
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงห้องแชทนี้")
        return redirect('game_dashboard', game_slug=next((g['slug'] for g in GAMES_LIST if g['name'] == post.game_name), 'index'))

    helpers = CustomUser.objects.filter(help_offered__post=post).distinct()

    participants = list(helpers)
    if post.user not in participants:
        participants.insert(0, post.user)

    context = {
        'post': post,
        'game_name': post.game_name,
        'is_owner': is_owner,
        'participants': participants, 
        'member_count': len(participants),
        'last_message_time': timezone.now().isoformat() 
    }
    return render(request, 'ashenone_app/chat_room.html', context)

@login_required(login_url='/')
def chat_list_view(request):
    user_related_posts = LFGPost.objects.get_user_related_posts(request.user)
    
    context = {
        'posts': user_related_posts,
    }
    return render(request, 'ashenone_app/chat_list.html', context)

@login_required(login_url='/')
@require_POST
def send_message_api(request, post_id):
    post = get_object_or_404(LFGPost, id=post_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Content cannot be empty'}, status=400)
    
    ChatMessage.objects.create(
        post=post,
        sender=request.user,
        content=content
    )
    
    return JsonResponse({'status': 'success', 'message': 'Message sent'})


@login_required(login_url='/')
def fetch_messages_api(request, post_id):
    post = get_object_or_404(LFGPost, id=post_id)
    
    messages_query = ChatMessage.objects.filter(post=post)
    
    messages_list = [
        {
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime("%H:%M:%S"),
            'is_me': msg.sender == request.user
        }
        for msg in messages_query
    ]
    
    return JsonResponse({'messages': messages_list, 'status': 'success'})

def content_detail(request, game_slug, content_slug):
    content = get_object_or_404(GuideContent, slug=content_slug)
    
    context = {
        'content': content,
        'game_slug': game_slug,
        'current_game_name': content.game_name
    }
    return render(request, 'ashenone_app/content_detail.html', context)

def user_profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    
    user_posts = LFGPost.objects.filter(user=profile_user).order_by('-created_at')
    
    helped_count = Offer.objects.filter(offered_by=profile_user).count()
    
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'helped_count': helped_count,
    }
    return render(request, 'ashenone_app/user_profile.html', context)

@login_required(login_url='/')
@require_POST 
def complete_lfg_post(request, post_id):
    post = get_object_or_404(LFGPost, id=post_id)
    
    if post.user != request.user:
        messages.error(request, "คุณไม่มีสิทธิ์ปิดงานโพสต์นี้")
        return redirect('chat_room', post_id=post.id)
    
    post.status = 'Completed'
    post.save()
    
    messages.success(request, "ปิดงานเรียบร้อย! ขอบคุณสำหรับการผจญภัย")
    
    return redirect('chat_room', post_id=post.id)

@login_required(login_url='/')
@require_POST
def report_user(request, username):
    """
    Action: รายงานผู้ใช้ (Report User)
    """
    target_user = get_object_or_404(CustomUser, username=username)
    
    # ป้องกันการ Report ตัวเอง
    if target_user == request.user:
        messages.error(request, "คุณไม่สามารถรายงานตัวเองได้")
        return redirect('user_profile', username=username)
        
    reason = request.POST.get('reason')
    details = request.POST.get('details')
    
    if not reason:
        messages.error(request, "กรุณาเลือกเหตุผลในการรายงาน")
        return redirect('user_profile', username=username)
        
    try:
        Report.objects.create(
            reporter=request.user,
            reported_user=target_user,
            reason=reason,
            details=details
        )
        messages.success(request, f"รายงานผู้ใช้ {target_user.username} เรียบร้อยแล้ว ทางทีมงานจะเร่งตรวจสอบ")
    except Exception as e:
        messages.error(request, "เกิดข้อผิดพลาดในการส่งรายงาน")
        logger.error(f"Report Error: {e}")
        
    return redirect('user_profile', username=username)