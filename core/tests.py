import os
import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Membership, File
from .image_detection import detect_faces
from django.conf import settings

User = get_user_model()

class CoreModelTests(TestCase):
    def test_user_creation_creates_membership_and_stripe_customer(self):
        # We might need to mock stripe here if we don't want actual API calls
        # But for now, let's see if it runs in the current environment
        email = "testuser@example.com"
        username = "testuser"
        user = User.objects.create_user(username=username, email=email, password="password123")
        
        self.assertTrue(user.stripe_customer_id.startswith('cus_'))
        
        membership = Membership.objects.get(user=user)
        self.assertEqual(membership.type, 'F')
        self.assertGreater(membership.end_date, timezone.now())

class ImageDetectionTests(TestCase):
    def setUp(self):
        # Create a dummy image for testing
        self.image_path = os.path.join(settings.MEDIA_ROOT, 'test_face.jpg')
        # Here we skip actual image creation for now and just check path resolution
        # or we could use a small base64 image if we wanted a real test.
    
    def test_detect_faces_handles_missing_file(self):
        result = detect_faces(image_path="non_existent_file.jpg")
        self.assertFalse(result['safely_executed'])
        self.assertIn("File not found", result['error_value'])
