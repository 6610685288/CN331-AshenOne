from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ashenone_app.models import CustomUser, LFGPost, GuideContent, Offer, ChatMessage, Report
import json
from django.contrib.messages.storage.base import Message
from django.urls import resolve

CustomUser = get_user_model()

class AshenOneFeatureTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.password = 'testpassword123' 
        
        self.user_a = CustomUser.objects.create_user(username='requester_a', password=self.password)
        self.user_b = CustomUser.objects.create_user(username='helper_b', password=self.password)
        self.admin_user = CustomUser.objects.create_superuser(username='testadmin', password=self.password, is_staff=True, is_superuser=True)

        self.game_slug = 'ds3'
        self.game_name = 'Dark Souls III'
        
        self.lfg_post = LFGPost.objects.create(
            user=self.user_a,
            game_name=self.game_name,
            platform='PC',
            boss_name='Test Boss for Offer',
            description='Testing Offer/Chat Post'
        )

        self.content_guide = GuideContent.objects.create(
            game_name=self.game_name,
            title='The Lore of Lothric',
            slug='the-lore-of-lothric-ds3',
            category='LORE',
            content_body='This content explains the deep lore.'
        )
        
        self.url_dashboard = reverse('game_dashboard', args=[self.game_slug])
        self.url_auth = reverse('handle_auth', args=[self.game_slug])
        self.url_post = reverse('handle_lfg_post')
        self.url_offer = reverse('offer_help', args=[self.lfg_post.id])
        self.url_chat = reverse('chat_room', args=[self.lfg_post.id])
        self.url_send_api = reverse('send_message_api', args=[self.lfg_post.id]) 
        self.url_fetch_api = reverse('fetch_messages_api', args=[self.lfg_post.id]) 
        self.url_content_detail = reverse('content_detail', args=[self.game_slug, self.content_guide.slug])
        self.url_complete = reverse('complete_lfg_post', args=[self.lfg_post.id])

    def test_01_register_happy_path(self):
        """Test U-1 (Happy Path): การลงทะเบียนสำเร็จ"""
        response = self.client.post(
            self.url_auth,
            {
                'action': 'register',
                'username': 'new_tarnished',
                'password': self.password,
                'confirm_password': self.password
            },
            follow=True 
        )
        self.assertContains(response, "ลงทะเบียนสำเร็จ!")

    def test_02_register_sad_path_password_mismatch(self):
        """Test U-1 (Sad Path): การลงทะเบียนล้มเหลว (Password ไม่ตรงกัน)"""
        response = self.client.post(
            self.url_auth,
            {   
                'action': 'register',
                'username': 'new_tarnished_2',
                'password': self.password,
                'confirm_password': 'password456' 
            },
            follow=True 
        )
        self.assertContains(response, "รหัสผ่านไม่ตรงกัน โปรดตรวจสอบอีกครั้ง")
        
    def test_03_login_happy_path(self):
        """Test U-1 (Happy Path): ล็อกอินสำเร็จ"""
        response = self.client.post(
            self.url_auth,
            { 'action': 'login', 'username': 'requester_a', 'password': self.password }
        )
        self.assertRedirects(response, self.url_dashboard)

    def test_04_login_sad_path_wrong_password(self):
        """Test U-1 (Sad Path): ล็อกอินล้มเหลว (Password ผิด)"""
        response = self.client.post(
            self.url_auth,
            { 'action': 'login', 'username': 'requester_a', 'password': 'wrongpassword' },
            follow=True
        )
        self.assertContains(response, "Username หรือ Password ไม่ถูกต้อง")

    def test_05_lfg_post_creation_happy_path(self):
        """Test U-2 (Happy Path): สร้างโพสต์ LFG สำเร็จ"""
        self.client.login(username='requester_a', password=self.password)
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
        self.assertContains(response, "สร้างโพสต์ LFG สำเร็จ!")
        self.assertEqual(LFGPost.objects.count(), initial_count + 1)

    def test_06_lfg_post_creation_sad_path_not_logged_in(self):
        """Test U-2 (Sad Path): สร้างโพสต์ LFG ล้มเหลว (ยังไม่ล็อกอิน)"""
        response = self.client.post(
            self.url_post,
            { 'bossName': 'Anonymous Boss' },
            follow=False
        )
        self.assertRedirects(response, f"{reverse('index')}?next={self.url_post}")

    def test_07_lfg_post_creation_sad_path_missing_field(self):
        """Test U-2 (Sad Path): สร้างโพสต์ LFG ล้มเหลว (ขาดข้อมูล Boss Name)"""
        self.client.login(username='requester_a', password=self.password)
        initial_count = LFGPost.objects.count()

        response = self.client.post(
            self.url_post,
            {
                'gameName': self.game_name,
                'platform': 'PC',
                'bossName': '', 
                'description': 'Help me!'
            },
            follow=True
        )
        
        self.assertContains(response, "กรุณากรอกชื่อบอสและรายละเอียดให้ครบถ้วน!")
        self.assertEqual(LFGPost.objects.count(), initial_count) 

    def test_08_lfg_view_correct_game_filtering(self):
        """Test U-2 (Happy Path): หน้า Dashboard แสดงโพสต์ที่กรองตามเกมที่ถูกต้อง"""
        LFGPost.objects.create(
            user=self.user_b,
            game_name='Elden Ring',
            platform='PS5',
            boss_name='Malenia',
            description='Testing Elden Ring'
        )
        
        response = self.client.get(self.url_dashboard) 
        self.assertContains(response, 'Test Boss for Offer') 
        self.assertNotContains(response, 'Malenia') 

    def test_09_offer_help_success_and_status_change(self):
        """Test U-4 (Happy Path): Offer สำเร็จ, สถานะเปลี่ยนเป็น 'In Progress'"""
        self.client.login(username='helper_b', password=self.password)
        
        response = self.client.post(self.url_offer, {}) 
        
        self.assertRedirects(response, self.url_chat)
        self.lfg_post.refresh_from_db()
        self.assertEqual(self.lfg_post.status, 'In Progress')

    def test_10_offer_help_sad_path_owner_self_offer(self):
        """Test U-4 (Sad Path): เจ้าของโพสต์พยายาม Offer ตัวเอง"""
        self.client.login(username='requester_a', password=self.password) 
        
        response = self.client.post(self.url_offer, {}, follow=True)
        
        self.assertContains(response, "ไม่สามารถเสนอช่วยเหลือโพสต์ที่คุณสร้างเองได้")
        self.assertEqual(Offer.objects.count(), 0)
        
    def test_11_offer_help_success_and_redirect(self):
        """Test U-4 (Happy Path): User B เสนอช่วยเหลือสำเร็จ และ Redirect ไป Chat Room"""
        self.client.login(username='helper_b', password=self.password)
        
        response = self.client.post(self.url_offer, {}) 
        
        self.assertRedirects(response, self.url_chat)
        
        self.assertTrue(Offer.objects.filter(post=self.lfg_post, offered_by=self.user_b).exists())

        self.lfg_post.refresh_from_db()
        self.assertEqual(self.lfg_post.status, 'In Progress')

    def test_12_offer_help_sad_path_user_already_offered(self):
        """Test U-4 (Sad Path): ผู้ใช้พยายามเสนอช่วยซ้ำ (ควร Redirect ไป Chat Room)"""
        Offer.objects.create(post=self.lfg_post, offered_by=self.user_b)
        self.client.login(username='helper_b', password=self.password)
        
        response = self.client.post(self.url_offer, {}) 
        
        self.assertRedirects(response, self.url_chat)
        self.assertEqual(Offer.objects.filter(post=self.lfg_post, offered_by=self.user_b).count(), 1)
    
    def test_13_chat_api_send_happy_path(self):
        """Test U-4 (Happy Path): การส่งข้อความ API สำเร็จ"""
        self.client.login(username='requester_a', password=self.password)
        initial_count = ChatMessage.objects.count()
        
        response = self.client.post(
            self.url_send_api,
            json.dumps({'content': 'Test message from Requester'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatMessage.objects.count(), initial_count + 1)

    def test_14_chat_api_fetch_happy_path(self):
        """Test U-4 (Happy Path): การดึงข้อความ API สำเร็จ (Polling)"""
        ChatMessage.objects.create(post=self.lfg_post, sender=self.user_a, content="First Message")
        self.client.login(username='helper_b', password=self.password)
        
        response = self.client.get(self.url_fetch_api)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['sender'], 'requester_a')
        self.assertFalse(data['messages'][0]['is_me'])
    
    def test_15_content_detail_public_access(self):
        """Test U-3 (Happy Path): Public สามารถเข้าถึงหน้ารายละเอียด Content ได้"""
        response = self.client.get(self.url_content_detail) 
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.content_guide.title)

    def test_16_admin_content_crud_creation(self):
        """Test A-1 (Admin CRUD): Admin สามารถสร้าง GuideContent ได้สำเร็จ"""
        self.client.login(username='testadmin', password=self.password)
        
        admin_add_url = reverse('admin:ashenone_app_guidecontent_add')
        
        response = self.client.post(
            admin_add_url,
            {
                'game_name': self.game_name,
                'title': 'Final Boss Guide',
                'slug': 'final-boss-guide',
                'category': 'BOSS',
                'content_body': 'Final strategy guide.',
                '_save': 'บันทึก'
            },
            follow=True
        )
        
        self.assertContains(response, "Final Boss Guide") 
        self.assertTrue(GuideContent.objects.filter(title='Final Boss Guide').exists())

    def test_17_admin_action_suspend_user(self):
        """Test A-3 (Admin): Admin สามารถ Suspend User ได้ และบล็อก Login"""
        self.client.login(username='testadmin', password=self.password)
        
        admin_url = reverse('admin:ashenone_app_customuser_changelist')
        response = self.client.post(admin_url, {
            'action': 'suspend_users',
            '_selected_action': [str(self.user_a.pk)] 
        }, follow=True)
        
        self.user_a.refresh_from_db()
        self.assertTrue(self.user_a.suspended) 
        
        self.client.logout()
        response = self.client.post(
            self.url_auth,
            { 'action': 'login', 'username': 'requester_a', 'password': self.password },
            follow=True
        )
        self.assertContains(response, "บัญชีของคุณถูกระงับการใช้งาน")

    def test_18_admin_action_delete_post(self):
            """Test A-2 (Admin): Admin สามารถลบโพสต์ LFG ได้"""
            self.client.login(username='testadmin', password=self.password)
            initial_count = LFGPost.objects.count()

            admin_changelist_url = reverse('admin:ashenone_app_lfgpost_changelist')

            response = self.client.post(
                admin_changelist_url,
                {
                    'action': 'delete_selected',
                    '_selected_action': [str(self.lfg_post.pk)]
                }
            )
            
            response = self.client.post(
                admin_changelist_url, 
                {
                    'action': 'delete_selected',
                    'post': 'yes', 
                    '_selected_action': [str(self.lfg_post.pk)]
                },
                follow=True 
            )
            
            self.assertEqual(LFGPost.objects.count(), initial_count - 1)
            self.assertFalse(LFGPost.objects.filter(pk=self.lfg_post.pk).exists())
    
    def test_19_profile_view_happy_path(self):
        """Test U-5 (Happy Path): เข้าดูหน้า Profile ของ User A ได้สำเร็จ"""
        url = reverse('user_profile', args=['requester_a'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "requester_a")
        self.assertContains(response, "Role: User")

    def test_20_profile_view_sad_path_user_not_found(self):
        """Test U-5 (Sad Path): เข้าดู Profile ของคนที่ไม่มีจริง (404)"""
        url = reverse('user_profile', args=['unknown_user'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- Complete Post (U-2 Maintenance) ---

    def test_21_complete_post_happy_path_owner(self):
        """Test (Happy Path): เจ้าของโพสต์กด Complete ได้สำเร็จ"""
        self.client.login(username='requester_a', password=self.password)
        response = self.client.post(self.url_complete, follow=True)
        self.assertEqual(response.status_code, 200)
        self.lfg_post.refresh_from_db()
        self.assertEqual(self.lfg_post.status, 'Completed')

    def test_22_complete_post_sad_path_non_owner(self):
        """Test (Sad Path): คนอื่น (Helper) พยายามกด Complete (ต้องถูกปฏิเสธ)"""
        self.client.login(username='helper_b', password=self.password)
        response = self.client.post(self.url_complete, follow=True)
        self.lfg_post.refresh_from_db()
        self.assertNotEqual(self.lfg_post.status, 'Completed')
        self.assertContains(response, "คุณไม่มีสิทธิ์ปิดงานโพสต์นี้")

    # --- Report System (A-4) ---

    def test_23_report_user_happy_path(self):
        """Test A-4 (Happy Path): รายงานผู้ใช้สำเร็จ"""
        self.client.login(username='helper_b', password=self.password)
        report_url = reverse('report_user', args=['requester_a'])
        response = self.client.post(report_url, {
            'reason': 'TOXIC',
            'details': 'User was rude in chat.'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "รายงานผู้ใช้ requester_a เรียบร้อยแล้ว")
        self.assertTrue(Report.objects.filter(reported_user=self.user_a, reason='TOXIC').exists())

    def test_24_report_user_sad_path_self_report(self):
        """Test A-4 (Sad Path): พยายามรายงานตัวเอง (ต้องถูกปฏิเสธ)"""
        self.client.login(username='helper_b', password=self.password)
        report_url = reverse('report_user', args=['helper_b']) 
        response = self.client.post(report_url, {
            'reason': 'SPAM',
            'details': 'Testing.'
        }, follow=True)
        self.assertContains(response, "คุณไม่สามารถรายงานตัวเองได้")
        self.assertFalse(Report.objects.filter(reported_user=self.user_b).exists())

    def test_25_report_user_sad_path_missing_reason(self):
        """Test A-4 (Sad Path): ส่งรายงานโดยไม่เลือกเหตุผล"""
        self.client.login(username='helper_b', password=self.password)
        
        report_url = reverse('report_user', args=['requester_a'])
        response = self.client.post(report_url, {
            'details': 'Just details without reason.'
        }, follow=True)
        
        self.assertContains(response, "กรุณาเลือกเหตุผลในการรายงาน")
        self.assertFalse(Report.objects.filter(reported_user=self.user_a).exists())