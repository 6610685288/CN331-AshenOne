
"""
Models (Data Logic) - AshenOne Django App (ORM Version)
(ไฟล์นี้คือไฟล์ที่ถูกต้องและสมบูรณ์ที่สุด)
"""
from django.db import models
from django.contrib.auth.models import AbstractUser

# --- GAME CONSTANTS (แหล่งข้อมูลสำหรับ View) ---
GAMES_LIST = [
    {'name': 'Dark Souls I', 'slug': 'ds1', 'logo_url': 'https://images2.alphacoders.com/895/895681.jpg'},
    {'name': 'Dark Souls II', 'slug': 'ds2', 'logo_url': 'https://i.redd.it/nfw7fzk7ye5b1.jpg'},
    {'name': 'Dark Souls III', 'slug': 'ds3', 'logo_url': 'https://cdn.wallpapersafari.com/76/54/ep5KaJ.jpg'},
    {'name': 'Bloodborne', 'slug': 'bb', 'logo_url': 'https://images.wallpapersden.com/image/download/bloodborne-game_a2tnaWyUmZqaraWkpJRobWllrWdobWY.jpg'},
    {'name': 'Sekiro', 'slug': 'sekiro', 'logo_url': 'https://mfiles.alphacoders.com/781/thumb-1920-781750.jpg'},
    {'name': 'Demon Souls', 'slug': 'demon-souls', 'logo_url': 'https://i.pinimg.com/736x/0f/ea/f1/0feaf19f38ed8232e2131bd9f4bf4ba7.jpg'},
    {'name': 'Elden Ring', 'slug': 'elden-ring', 'logo_url': 'https://preview.redd.it/y1udzivcql471.png?width=640&crop=smart&auto=webp&s=bd5d01bfcf84b8a1af55f89ed241ae99c9e91711'},
    {'name': 'Elden Ring: Nightreign', 'slug': 'elden-ring-nightreign', 'logo_url': 'https://i.pinimg.com/736x/a6/ee/f2/a6eef2a207daf54c78923542b45d2163.jpg'},
]

# --- 1. User Model (US-U1) ---
class CustomUser(AbstractUser):
    """
    โมเดลผู้ใช้หลัก
    สืบทอดจาก AbstractUser เพื่อใช้ระบบ Auth ของ Django
    (แก้ไข related_name เพื่อแก้ SystemCheckError)
    """
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('admin', 'Admin')], default='user')
    suspended = models.BooleanField(default=False)
    
   
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups', 
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions', 
        blank=True,
    )

    def __str__(self):
        return self.username

# --- 2. LFG Post Model (US-U2) ---
class LFGPost(models.Model):
    """
    โมเดลสำหรับ LFG Posts
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lfg_posts')
    game_name = models.CharField(max_length=100)
    platform = models.CharField(max_length=50)
    boss_name = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=10, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.game_name} - {self.boss_name} (by {self.user.username})"