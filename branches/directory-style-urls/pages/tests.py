# -*- coding: utf-8 -*-
from django.test import TestCase
import settings
from pages.models import *
from django.test.client import Client
from django.template import TemplateDoesNotExist

page_data = {'title':'test page', 'slug':'test-page-1', 'language':'en',
    'sites':[2], 'status':Page.PUBLISHED}


class PagesTestCase(TestCase):
    fixtures = ['tests.json']

    def test_01_add_page(self):
        """
        Test that the add admin page could be displayed via the admin
        """
        c = Client()
        c.login(username= 'batiste', password='b')
        response = c.get('/admin/pages/page/add/')
        assert(response.status_code == 200)


    def test_02_create_page(self):
        """
        Test that a page can be created via the admin
        """
        c = Client()
        c.login(username= 'batiste', password='b')
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        site = Site.objects.get(id=2)
        slug_content = Content.objects.get_content_slug_by_slug(page_data['slug'], site)
        assert(slug_content is not None)
        page = slug_content.page
        assert(page.title() == page_data['title'])
        assert(page.slug() == page_data['slug'])

    # not relevant now with this branch
    '''
    def test_03_slug_collision(self):
        """
        Test a slug collision
        """
        c = Client()
        site = Site.objects.get(id=2)
        c.login(username= 'batiste', password='b')
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        page1 = Content.objects.get_content_slug_by_slug(page_data['slug'], site).page

        response = c.post('/admin/pages/page/add/', page_data)
        assert(response.status_code == 200)

        settings.PAGE_UNIQUE_SLUG_REQUIRED = False
        response = c.post('/admin/pages/page/add/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        page2 = Content.objects.get_content_slug_by_slug(page_data['slug'], site).page
        assert(page1.id != page2.id)
    '''

    def test_04_details_view(self):
        """
        Test the details view
        """

        c = Client()
        c.login(username= 'batiste', password='b')
        try:
            response = c.get('/pages/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data['status'] = Page.DRAFT
        response = c.post('/admin/pages/page/add/', page_data)
        try:
            response = c.get('/pages/')
        except TemplateDoesNotExist, e:
            if e.args != ('404.html',):
                raise

        page_data['status'] = Page.PUBLISHED
        page_data['slug'] = 'test-page-2'
        response = c.post('/admin/pages/page/add/', page_data)
        response = c.get('/admin/pages/page/')
        
        response = c.get('/pages/')
        assert(response.status_code == 200)

    def test_05_edit_page(self):
        """
        Test that a page can edited via the admin
        """
        c = Client()
        c.login(username= 'batiste', password='b')
        response = c.post('/admin/pages/page/add/', page_data)
        response = c.get('/admin/pages/page/1/')
        assert(response.status_code == 200)
        page_data['title'] = 'changed title'
        response = c.post('/admin/pages/page/1/', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        page = Page.objects.get(id=1)
        assert(page.title() == 'changed title')
        

    def test_06_parent_slug(self):
        """
        Test the diretory slugs branch
        """
        c = Client()
        site = Site.objects.get(id=2)
        c.login(username= 'batiste', password='b')
        
        page_data['title'] = 'parent title'
        response = c.post('/admin/pages/page/add/', page_data)
        # the redirect tell that the page has been create correctly
        self.assertRedirects(response, '/admin/pages/page/')

        page_data['title'] = 'parent title'
        response = c.post('/admin/pages/page/add/', page_data)
        # we cannot create 2 root page with the same slug
        # this assert test that the creation fail correctly
        assert(response.status_code == 200)

        page1 = Content.objects.get_content_slug_by_slug(page_data['slug'], site).page
        assert(page1.id == 1)

        page_data['title'] = 'children title'
        # TODO:  this post fail with the get parameters, please find a fix
        response = c.post('/admin/pages/page/add/?target=1&position=first-child', page_data)
        self.assertRedirects(response, '/admin/pages/page/')
        
        # finaly test that we can get every page according the path
        response = c.get('/pages/test-page-1/')
        self.assertContains(response, "parent title", status_code == 200)
        
        response = c.get('/pages/test-page-1/test-page-1/')
        self.assertContains(response, "children title", status_code == 200)
                 