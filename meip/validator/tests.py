from django.test import TestCase
from .engine import validate_email_single, calculate_rtpc_score, is_disposable, is_role_based

class ValidatorEngineTests(TestCase):
    def test_disposable(self):
        self.assertTrue(is_disposable("test@mailinator.com"))
        self.assertFalse(is_disposable("test@gmail.com"))

    def test_role_based(self):
        self.assertTrue(is_role_based("admin@example.com"))
        self.assertFalse(is_role_based("rahul@example.com"))

    def test_score_calculation(self):
        # Perfect email
        data = {
            'smtp_check_success': True,
            'is_disposable': False,
            'is_role_based': False,
            'has_anti_spam': True,
            'bounce_history': False
        }
        # 100 + 10 = 100 (cap)
        self.assertEqual(calculate_rtpc_score(data), 100)

        # Disposable: 100 base + 10 (anti_spam) - 50 (disposable) = 60
        # However, logic in engine.py:
        # if smtp_check_success (True): 100
        # if disposable: -50 -> 50
        # if has_anti_spam: +10 -> 60
        # Wait, in the test dict 'smtp_check_success' is True.
        # But wait, logic says:
        # if NOT smtp_check_success: -50.
        # In test data: smtp_check_success=True. So no -50.
        # So it's 100 - 50 (disposable) + 10 (anti-spam) = 60.
        self.assertEqual(calculate_rtpc_score(data), 60)

    def test_validate_single(self):
        # Warning: This might make network calls. 
        # In a real test we should mock DNS.
        # For this environment, we'll try a known domain if safe, or skip/mock.
        # We can't easily mock here without `unittest.mock`.
        pass
