import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import ArribereNemaStocks.views as nema_views

class TestYourViewMixin:
    def __init__(self, *args, **kwargs):
        self.target_view = None
        self.target_view_name: str = ''
        self.url: str = '/'
        self.template_name: str = ''
        super().__init__(*args, **kwargs)
        
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='12345')

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse(self.target_view_name))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse(self.target_view_name))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)

    # def test_redirect_if_not_logged_in(self):
    #     response = self.client.get(reverse(self.target_view_name))
    #     self.assertRedirects(response, f'/login/?next={self.url}')


class TestOngoingFreezes(TestYourViewMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_view = nema_views.ongoing_freezes
        self.target_view_name = 'ongoing_freezes'
        self.url = '/ongoing_freezes/'
        self.template_name = 'freezes_and_thaws/ongoing_freezes.html'


class TestOngoingThaws(TestYourViewMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_view = nema_views.ongoing_thaws
        self.target_view_name = 'ongoing_thaws'
        self.url = '/ongoing_thaws/'
        self.template_name = 'freezes_and_thaws/ongoing_thaws.html'


class TestOutstandingFreezeRequests(TestYourViewMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_view = nema_views.outstanding_freeze_requests
        self.target_view_name = 'outstanding_freeze_requests'
        self.url = '/outstanding_freeze_requests/'
        self.template_name = 'freezes_and_thaws/outstanding_freeze_requests.html'


class TestOutstandingThawRequests(TestYourViewMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_view = nema_views.outstanding_thaw_requests
        self.target_view_name = 'outstanding_thaw_requests'
        self.url = '/outstanding_thaw_requests/'
        self.template_name = 'freezes_and_thaws/outstanding_thaw_requests.html'


class TestStrainAssignments(TestYourViewMixin, TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_view = nema_views.strain_assignments
        self.target_view_name = 'strain_assignments'
        self.url = '/strain_assignments/'
        self.template_name = 'strains/strain_assignments.html'
