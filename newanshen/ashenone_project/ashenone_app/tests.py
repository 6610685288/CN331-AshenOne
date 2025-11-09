# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from ashenone_app.models import CustomUser, LFGPost, GAMES_LIST
from unittest.mock import patch, Mock

User = get_user_model() # ใช้ CustomUser ที่เรากำหนดไว้

class AshenOneViewsTestCase(TestCase):
    
    def setUp(self):
        # สร้าง Client และ User สำหรับทดสอบ
        self.client = Client()
        # CustomUser.objects.create_user จะใช้ hashing password ให้
        self.user = CustomUser.objects.create_user(username='testuser', password='testpassword123', role='user')
        self.admin_user = CustomUser.objects.create_user(username='adminuser', password='adminpassword123', role='admin', is_staff=True, is_superuser=True)

        self.game_slug = 'ds3'
        self.game_name = 'Dark Souls III'
        
        # สร้างโพสต์ LFG สำหรับการทดสอบ
        self.lfg_post = LFGPost.objects.create(
            user=self.user,
            game_name=self.game_name,
            platform='PC',
            boss_name='Test Boss',
            description='Testing LFG Post'
        )

        # URLS ที่จะใช้
        self.url_dashboard = reverse('game_dashboard', args=[self.game_slug])
        self.url_auth = reverse('handle_auth', args=[self.game_slug])
        self.url_post = reverse('handle_lfg_post')
        self.url_admin = reverse('admin:ashenone_app_customuser_changelist')


    # ---------------------------------------------------
    # --- I. Test US-U1 (Authentication & Register) ---
    # ---------------------------------------------------

    def test_01_register_happy_path(self):
        response = self.client.post(
            self.url_auth,
            {
                'action': 'register',
                'username': 'new_tarnished',
                'password': 'password123',
                'confirm_password': 'password123'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200) # 200 after redirect
        self.assertContains(response, "ลงทะเบียนสำเร็จ!")
        self.assertTrue(CustomUser.objects.filter(username='new_tarnished').exists())
        self.assertTrue(response.context['user'].is_authenticated)

    def test_02_register_sad_path_password_mismatch(self):
        response = self.client.post(
            self.url_auth,
            {
                'action': 'register',
                'username': 'new_tarnished_2',
                'password': 'password123',
                'confirm_password': 'password456' # <-- Mismatch
            },
            follow=True
        )
        self.assertContains(response, "รหัสผ่านไม่ตรงกัน โปรดตรวจสอบอีกครั้ง")
        self.assertFalse(CustomUser.objects.filter(username='new_tarnished_2').exists())

    def test_03_login_happy_path(self):
        response = self.client.post(
            self.url_auth,
            {
                'action': 'login',
                'username': 'testuser',
                'password': 'testpassword123'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Out') # User sees sign out button
        self.assertTrue(response.context['user'].is_authenticated)

    def test_04_login_sad_path_wrong_password(self):
        response = self.client.post(
            self.url_auth,
            {
                'action': 'login',
                'username': 'testuser',
                'password': 'wrongpassword'
            },
            follow=True
        )
        self.assertContains(response, "Username หรือ Password ไม่ถูกต้อง")
        self.assertFalse(response.context['user'].is_authenticated)

    # ---------------------------------------------------
    # --- II. Test US-U2 (LFG Post Creation) ---
    # ---------------------------------------------------

    def test_05_lfg_post_creation_happy_path(self):
        self.client.login(username='testuser', password='testpassword123')
        
        initial_count = LFGPost.objects.count()

        response = self.client.post(
            self.url_post,
            {
                'gameName': self.game_name,
                'platform': 'PC',
                'bossName': 'New Boss',
                'description': 'Help me!'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "สร้างโพสต์ LFG สำเร็จ!")
        self.assertEqual(LFGPost.objects.count(), initial_count + 1)
        self.assertTrue(LFGPost.objects.filter(boss_name='New Boss').exists())

    def test_06_lfg_post_creation_sad_path_not_logged_in(self):
        response = self.client.post(
            self.url_post,
            { 'bossName': 'Anonymous Boss' },
            follow=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('index')))

    def test_07_lfg_post_creation_sad_path_missing_field(self):
        self.client.login(username='testuser', password='testpassword123')
        initial_count = LFGPost.objects.count()

        response = self.client.post(
            self.url_post,
            {
                'gameName': self.game_name,
                'platform': 'PC',
                'bossName': '', # <-- Missing
                'description': 'Help me!'
            },
            follow=True
        )
        self.assertContains(response, "กรุณากรอกชื่อบอสและรายละเอียดให้ครบถ้วน!")
        self.assertEqual(LFGPost.objects.count(), initial_count) # Count must not increase
        
    # ---------------------------------------------------
    # --- III. Test US-U3 (Content Access) & Filtering ---
    # ---------------------------------------------------
    
    def test_08_lfg_view_correct_game_filtering(self):
    
        LFGPost.objects.create(
            user=self.user,
            game_name='Elden Ring',
            platform='PS5',
            boss_name='Malenia',
            description='Help me!'
        )
    
        response = self.client.get(self.url_dashboard) 
        
        self.assertContains(response, 'Test Boss') 
        self.assertNotContains(response, 'Malenia')

    # ---------------------------------------------------
    # --- IV. Test US-A2 & A-3 (Admin Actions) ---
    # ---------------------------------------------------

    def test_09_admin_action_suspend_user(self):
        """Test US-A3 (Admin): Admin สามารถ Suspend User ได้"""
       
        self.client.login(username='testadmin', password='adminpassword123')
        
       
        admin_user_changelist_url = reverse('admin:ashenone_app_customuser_changelist')
        
     
        response = self.client.post(admin_user_changelist_url, {
            'action': 'suspend_users',
            '_selected_action': [str(self.user.pk)] 
        }, follow=True)
        
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.suspended)
        self.assertContains(response, "Suspended selected users") 
        
        
        self.client.logout()
        response = self.client.post(
            self.url_auth,
            { 'action': 'login', 'username': 'testuser', 'password': 'testpassword123' },
            follow=True
        )
        self.assertContains(response, "บัญชีของคุณถูกระงับการใช้งาน")

    def test_10_admin_action_delete_post(self):
        self.client.login(username='testadmin', password='adminpassword123')
        
        
        admin_post_changelist_url = reverse('admin:ashenone_app_lfgpost_changelist')
        
        
        initial_count = LFGPost.objects.count()

        response = self.client.post(admin_post_changelist_url, {
            'action': 'delete_selected',
            '_selected_action': [str(self.lfg_post.pk)]
        }, follow=True)
        

        self.assertEqual(LFGPost.objects.count(), initial_count - 1)
        self.assertFalse(LFGPost.objects.filter(pk=self.lfg_post.pk).exists())
        self.assertContains(response, "Successfully deleted 1 LFG post")