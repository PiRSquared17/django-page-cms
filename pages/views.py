from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import SITE_CACHE
from django.core.urlresolvers import reverse

from pages import settings
from pages.models import Page, Content, URL
from pages.utils import auto_render, get_template_from_request, get_language_from_request

import re

def details(request, page_id=None, slug=None, 
        template_name=settings.DEFAULT_PAGE_TEMPLATE):    
    lang = get_language_from_request(request)
    site = request.site
    pages = Page.objects.root(site).order_by("tree_id")
    if pages:
        if page_id:
            current_page = get_object_or_404(Page.objects.published(site), pk=page_id)
        elif slug:
            try:
                relative_url = re.sub(r'^%s' % reverse('pages-root'), '', request.path)
                current_page = URL.objects.filter(
                                   url=relative_url
                               ).latest('creation_date').page
            except URL.DoesNotExist:
                raise Http404
        else:
            current_page = pages[0]
        template_name = get_template_from_request(request, current_page)
    else:
        current_page = None
    return template_name, locals()
details = auto_render(details)

