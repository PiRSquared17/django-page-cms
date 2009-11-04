# -*- coding: utf-8 -*-
"""Django page CMS ``models``."""
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
import mptt
from pages.utils import get_placeholders, normalize_url
from pages.pagelinks import update_broken_links
from pages.managers import PageManager, ContentManager, \
         PagePermissionManager, PageAliasManager
from pages import settings


class Page(models.Model):
    """
    This model contain the status, dates, author, template.
    The real content of the page can be found in the
    :class:`Content <pages.models.Content>` model.

    .. attribute:: creation_date
    When the page has been created.

    .. attribute:: publication_date
    When the page should be visible.

    .. attribute:: publication_end_date
    When the publication of this page end.

    .. attribute:: last_modification_date
    Last time this page has been modified.

    .. attribute:: status
    The current status of the page. Could be DRAFT, PUBLISHED,
    EXPIRED or HIDDEN. You should the property :attr:`calculated_status` if
    you want that the dates are taken in account.

    .. attribute:: template
    A string containing the name of the template file for this page.
    """
    
    # some class constants to refer to, e.g. Page.DRAFT
    DRAFT = 0
    PUBLISHED = 1
    EXPIRED = 2
    HIDDEN = 3
    STATUSES = (
        (PUBLISHED, _('Published')),
        (HIDDEN, _('Hidden')),
        (DRAFT, _('Draft')),
    )

    PAGE_LANGUAGES_KEY = "page_%d_languages"
    PAGE_URL_KEY = "page_%d_language_%s_url"
    #PAGE_TEMPLATE_KEY = "page_%d_template"
    #PAGE_CHILDREN_KEY = "page_children_%d_%d"
    PAGE_CONTENT_DICT_KEY = "page_content_dict_%d_%s"
    PAGE_BROKEN_LINK_KEY = "page_broken_link_%s"

    author = models.ForeignKey(User, verbose_name=_('author'))
    
    parent = models.ForeignKey('self', null=True, blank=True, 
            related_name='children', verbose_name=_('parent'))
    creation_date = models.DateTimeField(_('creation date'), editable=False, 
            default=datetime.now)
    publication_date = models.DateTimeField(_('publication date'), 
            null=True, blank=True, help_text=_('''When the page should go live.
            Status must be "Published" for page to go live.'''))
    publication_end_date = models.DateTimeField(_('publication end date'), 
            null=True, blank=True, help_text=_('''When to expire the page.
            Leave empty to never expire.'''))

    last_modification_date = models.DateTimeField(_('last modification date'))

    status = models.IntegerField(_('status'), choices=STATUSES, default=DRAFT)
    template = models.CharField(_('template'), max_length=100, null=True,
            blank=True)
    
    # Disable could make site tests fail
    sites = models.ManyToManyField(Site, default=[settings.SITE_ID], 
            help_text=_('The site(s) the page is accessible at.'),
            verbose_name=_('sites'))
    redirect_to_url = models.CharField(max_length=200, null=True, blank=True)

    redirect_to = models.ForeignKey('self', null=True, blank=True,
            related_name='redirected_pages')

    if settings.PAGE_LINK_EDITOR:
        # If this page contain links to other pages, the pages will be added here
        pagelink = models.CharField(_('page IDs with links to this page'),
            max_length=200, null=True, blank=True)
        # Count all the internal broken links
        pagelink_broken = models.PositiveSmallIntegerField(
            _('number of broken page links found'), null=True, blank=True)
        # Count all the external broken links
        externallink_broken = models.PositiveSmallIntegerField(
            _('number of broken URLs found'), null=True, blank=True)
    
    # Managers
    objects = PageManager()

    if settings.PAGE_TAGGING:
        from tagging import fields
        tags = fields.TagField(null=True)

    class Meta:
        """Make sure the default page ordering is correct."""
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def save(self, *args, **kwargs):
        """Override the default ``save`` method."""
        if not self.status:
            self.status = self.DRAFT
        # Published pages should always have a publication date
        if self.publication_date is None and self.status == self.PUBLISHED:
            self.publication_date = datetime.now()
        # Drafts should not, unless they have been set to the future
        if self.status == self.DRAFT:
            if settings.PAGE_SHOW_START_DATE:
                if self.publication_date and self.publication_date <= datetime.now():
                    self.publication_date = None
            else:
                self.publication_date = None
        self.last_modification_date = datetime.now()
        super(Page, self).save(*args, **kwargs)

    def _get_calculated_status(self):
        """Get the calculated status of the page based on
        :attr:`Page.publication_date`,
        :attr:`Page.publication_end_date`,
        and :attr:`Page.status`."""
        if settings.PAGE_SHOW_START_DATE and self.publication_date:
            if self.publication_date > datetime.now():
                return self.DRAFT

        if settings.PAGE_SHOW_END_DATE and self.publication_end_date:
            if self.publication_end_date < datetime.now():
                return self.EXPIRED

        return self.status
    calculated_status = property(_get_calculated_status)

    def delete(self, *args, **kwargs): 
        """
        Set class :attr:`pagelink_broken` of all `a` tags contained in Content
        objects. Then clear :attr:`pagelink` from this page ID in other pages.
        """
        if not settings.PAGE_LINK_EDITOR:
            super(Page, self).delete(*args, **kwargs)
            return
        if self.pagelink is not None:
            pagelink_ids = self.pagelink.split(',')
            if pagelink_ids and pagelink_ids[0] !='':
                for pk, obj in Page.objects.in_bulk(pagelink_ids).items():
                    if obj.id != self.id:
                        update_broken_links(self, obj, Content)

        # update all pagelink (pages ID list) if contening the 'page_ID' 
        PAGE_LIST_ID_REGEX = r',?'+str(self.id)+r',?'
        for obj in Page.objects.filter(pagelink__regex=PAGE_LIST_ID_REGEX):
            if obj.id != self.id:
                if obj.pagelink is not None:
                    obj_pagelink_ids = obj.pagelink.split(',')
                    if obj_pagelink_ids and obj_pagelink_ids[0] !='':
                        if str(self.id) in obj_pagelink_ids:
                            obj_pagelink_ids.remove(str(self.id))
                            if obj_pagelink_ids and obj_pagelink_ids[0] !='':
                                obj.pagelink = obj_pagelink_ids
                            else:
                                obj.pagelink = ''
                            obj.save()
        super(Page, self).delete(*args, **kwargs)

    def get_children_for_frontend(self):
        """Return a :class:`QuerySet` of published children page"""
        return Page.objects.filter_published(self.get_children())

    def invalidate(self):
        """Invalidate cached data for this page."""

        cache.delete(self.PAGE_LANGUAGES_KEY % (self.id))
        #cache.delete(self.PAGE_TEMPLATE_KEY % (self.id))

        p_names = [p.name for p in get_placeholders(self.get_template())]
        if 'slug' not in p_names:
            p_names.append('slug')
        if 'title' not in p_names:
            p_names.append('title')
        for name in p_names:
            cache.delete(self.PAGE_CONTENT_DICT_KEY % (self.id, name))

        for lang in settings.PAGE_LANGUAGES:
            cache.delete(self.PAGE_URL_KEY % (self.id, lang[0]))
        cache.delete(self.PAGE_URL_KEY % (self.id, "None"))

    def get_languages(self):
        """
        Return a list of all used languages for this page.
        """
        languages = cache.get(self.PAGE_LANGUAGES_KEY % (self.id))
        if languages:
            return languages

        languages = [c['language'] for
                            c in Content.objects.filter(page=self,
                            type="slug").values('language')]
        languages = list(set(languages)) # remove duplicates
        languages.sort()
        cache.set(self.PAGE_LANGUAGES_KEY % (self.id), languages)
        return languages

    def is_first_root(self):
        """Return ``True`` if the page is the first root page."""
        if self.parent:
            return False
        return Page.objects.root()[0].id == self.id

    def has_broken_link(self):
        """
        Return ``True`` if the page have broken links to other pages
        into the content.
        """
        return cache.get(self.PAGE_BROKEN_LINK_KEY % self.id)

    def get_absolute_url(self, language=None, in_cache=True):
        """Return the absolute page url. Add the language prefix if
        ``PAGE_USE_LANGUAGE_PREFIX`` setting is set to ``True``.

        :param language: the wanted url language.
        """
        url = reverse('pages-root')
        if settings.PAGE_USE_LANGUAGE_PREFIX:
            url += str(language) + u'/'
        return url + self.get_url(language, in_cache)

    def get_url(self, language=None, in_cache=True):
        """Return url of this page, adding all parent's slug."""
        if in_cache:
            url = cache.get(self.PAGE_URL_KEY % (self.id, language))
            if url:
                return url
        if settings.PAGE_HIDE_ROOT_SLUG and self.is_first_root():
            url = ''
        else:
            url = u'%s' % self.slug(language)
        for ancestor in self.get_ancestors(ascending=True):
            url = ancestor.slug(language) + u'/' + url

        if settings.PAGE_HIDE_ROOT_SLUG and self.is_first_root():
            url = url
        elif not url.endswith('/'):
            url = url + u'/'

        cache.set(self.PAGE_URL_KEY % (self.id, language), url)
        
        return url

    def slug(self, language=None, fallback=True):
        """
        Return the slug of the page depending on the given language.

        :param language: wanted language, if not defined default is used.
        :param fallback: if ``True``, the slug will also be searched in other \
        languages.
        """
        
        slug = Content.objects.get_content(self, language, 'slug',
                                           language_fallback=fallback)

        return slug

    def title(self, language=None, fallback=True):
        """
        Return the title of the page depending on the given language.

        :param language: wanted language, if not defined default is used.
        :param fallback: if ``True``, the slug will also be searched in other \
        languages.
        """
        if not language:
            language = settings.PAGE_DEFAULT_LANGUAGE
            
        return Content.objects.get_content(self, language, 'title',
                                           language_fallback=fallback)

    def get_template(self):
        """
        Get the :attr:`template <Page.template>` of this page if
        defined or the closer parent's one if defined
        or :attr:`pages.settings.DEFAULT_PAGE_TEMPLATE` otherwise.
        """
        if self.template:
            return self.template

        template = None
        for p in self.get_ancestors(ascending=True):
            if p.template:
                template = p.template
                break

        if not template:
            template = settings.DEFAULT_PAGE_TEMPLATE

        return template

    def get_template_name(self):
        """
        Get the template name of this page if defined or if a closer
        parent has a defined template or
        :data:`pages.settings.DEFAULT_PAGE_TEMPLATE` otherwise.
        """
        template = self.get_template()
        for  t in settings.PAGE_TEMPLATES:
            if t[0] == template:
                return t[1]
        return template
        
    def has_page_permission(self, request):
        """
        Return ``True`` if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if not settings.PAGE_PERMISSION:
            return True
        else:
            permission = PagePermission.objects.get_page_id_list(request.user)
            if permission == "All":
                return True
            if self.id in permission:
                return True
            return False

    def valid_targets(self, perms="All"):
        """Return a :class:`QuerySet` of valid targets for moving a page
        into the tree.

        :param perms: the level of permission of the concerned user.
        """
        exclude_list = [self.id]
        for p in self.get_descendants():
            exclude_list.append(p.id)
        if perms != "All":
            return Page.objects.filter(id__in=perms).exclude(
                                                id__in=exclude_list)
        else:
            return Page.objects.exclude(id__in=exclude_list)

    def slug_with_level(self, language=None):
        """Display the slug of the page prepended with insecable
        spaces equal to the level of page in the hierarchy."""
        level = ''
        if self.level:
            for n in range(0, self.level):
                level += '&nbsp;&nbsp;&nbsp;'
        return mark_safe(level + self.slug(language))
        
    def margin_level(self):
        return self.level * 2

    def __unicode__(self):
        if self.id:
            slug = self.slug()
        else:
            return "Page %s" % self.id
        return slug

# Don't register the Page model twice.
try:
    mptt.register(Page)
except mptt.AlreadyRegistered:
    pass

if settings.PAGE_PERMISSION:
    class PagePermission(models.Model):
        """
        Page permission object
        """
        TYPES = (
            (0, _('All')),
            (1, _('This page only')),
            (2, _('This page and all children')),
        )
        page = models.ForeignKey(Page, null=True, blank=True,
                verbose_name=_('page'))
        user = models.ForeignKey(User, verbose_name=_('user'))
        type = models.IntegerField(_('type'), choices=TYPES, default=0)

        objects = PagePermissionManager()

        class Meta:
            verbose_name = _('page permission')
            verbose_name_plural = _('page permissions')

        def __unicode__(self):
            return "%s :: %s" % (self.user,
                    unicode(PagePermission.TYPES[self.type][1]))

class Content(models.Model):
    """A block of content, tied to a :class:`Page <pages.models.Page>`,
    for a particular language"""
    
    # languages could have five characters : Brazilian Portuguese is pt-br
    language = models.CharField(_('language'), max_length=5, blank=False)
    body = models.TextField(_('body'))
    type = models.CharField(_('type'), max_length=100, blank=False)
    page = models.ForeignKey(Page, verbose_name=_('page'))

    creation_date = models.DateTimeField(_('creation date'), editable=False,
            default=datetime.now)
    objects = ContentManager()

    class Meta:
        get_latest_by = 'creation_date'
        verbose_name = _('content')
        verbose_name_plural = _('contents')

    def __unicode__(self):
        return "%s :: %s" % (self.page.slug(), self.body[0:15])

class PageAlias(models.Model):
    """URL alias for a :class:`Page <pages.models.Page>`"""
    page = models.ForeignKey(Page, null=True, blank=True, verbose_name=_('page'))
    url = models.CharField(max_length=255, unique=True)
    objects = PageAliasManager()
    class Meta:
        verbose_name_plural = _('Aliases')
    
    def save(self, *args, **kwargs):
        # normalize url
        self.url = normalize_url(self.url)
        super(PageAlias, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return "%s => %s" % (self.url, self.page.get_url())
