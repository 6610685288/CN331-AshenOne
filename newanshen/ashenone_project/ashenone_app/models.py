from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import uuid
from django.db.models import Q

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

GAME_CHOICES = [(game['name'], game['name']) for game in GAMES_LIST] 
PLATFORM_CHOICES = [('PC', 'PC'), ('PS5', 'PlayStation 5'), ('XBOX', 'Xbox Series X/S')]
STATUS_CHOICES = (
    ('Active', 'Active'),
    ('In Progress', 'In Progress'),
    ('Completed', 'Completed'), 
)

class CustomUser(AbstractUser):
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

class LFGPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lfg_posts')
    game_name = models.CharField(max_length=100)
    platform = models.CharField(max_length=50)
    boss_name = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=10, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    class LFGPostManager(models.Manager):
        def get_user_related_posts(self, user):
            return self.filter(
                Q(user=user) | Q(offers__offered_by=user)
            ).distinct().order_by('-created_at')
            
    objects = LFGPostManager() 

    def __str__(self):
        return f"{self.game_name} - {self.boss_name} (by {self.user.username})"
    
class Offer(models.Model):
    post = models.ForeignKey(LFGPost, on_delete=models.CASCADE, related_name='offers')
    offered_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='help_offered')
    message = models.TextField(blank=True, null=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'offered_by') 

    def __str__(self):
        return f"Offer by {self.offered_by.username} on {self.post.boss_name}"

class ChatMessage(models.Model):
    post = models.ForeignKey(LFGPost, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} on {self.post.boss_name}"
    
class GuideContent(models.Model):
    CONTENT_CHOICES = (
        ('LORE', 'Lore Summary'),
        ('BOSS', 'Boss Guide'),
        ('BUILD', 'Build Guide'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_name = models.CharField(max_length=100, choices=GAME_CHOICES)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200) 
    category = models.CharField(max_length=10, choices=CONTENT_CHOICES)
    content_body = models.TextField() 
    updated_at = models.DateTimeField(auto_now=True) 
    
    class Meta:
        ordering = ['game_name', 'title']

    def __str__(self):
        return f"[{self.category}] {self.title} ({self.game_name})"