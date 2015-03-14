# Backwards Incompatible Changes #

Latest changes in the CHANGELOG file:

http://github.com/batiste/django-page-cms/blob/master/CHANGELOG

### [r598](https://code.google.com/p/django-page-cms/source/detail?r=598) (Jul 08, 2009) ###

The signature of the default view has changed:

```
-def details(request, slug=None, lang=None):
+def details(request, path=None, lang=None):
```

Consequently, if you had add a customized urls.py you will need to update it to

```
if settings.PAGE_USE_LANGUAGE_PREFIX:
    urlpatterns += patterns('',
        url(r'^(?P<lang>[-\w]+)/(?P<path>.*)$', details,
            name='pages-details-by-slug'),
    )
else:
    urlpatterns += patterns('',
        url(r'^(?P<path>.*)$', details,
            name='pages-details-by-slug'),
    )
```

### [r569](https://code.google.com/p/django-page-cms/source/detail?r=569) (Jun 16, 2009) ###

Now overriding a template block containing with a placeholder will work remove it from the admin. In example:

index.html
```
{% block override %}
    <!-- nice.html overrideing this block to make custom-widget-example disapear form the admin -->
    {% placeholder custom-widget-example on current_page with example.widgets.CustomTextarea parsed  %}
{% endblock %}
```

nice.html
```
{% block override %}
    <!-- by overrideing this block custom-widget-example should disapear form the admin -->
{% endblock %}
```

### [r450](https://code.google.com/p/django-page-cms/source/detail?r=450) (Apr 15, 2009) ###
last\_modification\_date (models.DateTimeField) has been added to the Page model.

```
BEGIN;
ALTER TABLE pages_page
    ADD COLUMN last_modification_date datetime;
COMMIT;
```

### [r430](https://code.google.com/p/django-page-cms/source/detail?r=430) (Apr 2, 2009) ###
Page redirection has been added to the code base. Page Model change and DB synchronisation is needed.

The TinyMCE widget is now handle by the very good [django-tinymce project](http://code.google.com/p/django-tinymce/). you can enable it in your settings with PAGE\_TINYMCE to True (default: False).

### [r399](https://code.google.com/p/django-page-cms/source/detail?r=399) (Marsh 14, 2009) ###

Directory like URLs has been added to the code base. Now if you set PAGE\_UNIQUE\_SLUG\_REQUIRED to False you will get this directory like URLs instead of the the id trick at the end of the page name.

### [r399](https://code.google.com/p/django-page-cms/source/detail?r=399) (Marsh 14, 2009) ###

Directory like URLs has been added to the code base. Now if you set PAGE\_UNIQUE\_SLUG\_REQUIRED to False you will get this directory like URLs instead of the the id trick at the end of the page name.

### [r368](https://code.google.com/p/django-page-cms/source/detail?r=368) (Feb 25, 2009) ###

The Content model accept now languages described with 5 characters to accept language of the form "en-us".

You can face some problems if you were already describing languages with 5 characters in settings.LANGUAGES or settings.PAGE\_LANGUAGES. The new pages will be saved in the database with 5 characters and the old one would remain with the old 2 characters language code.

**Quick fix** : set your languages in settings.PAGE\_LANGUAGES with only 2 characters.

To update to 5 characters alter your pages.content.language database field to accept 5 characters and update every content to the targeted new language code, ie: "en" becomes "en-us".

### [r361](https://code.google.com/p/django-page-cms/source/detail?r=361) (Feb 22, 2009) ###

The site middle ware has been removed from the code source. Update your settings:

**Solution**: remove 'pages.middleware.CurrentSiteMiddleware' from your MIDDLEWARE\_CLASSES.


### [r285](https://code.google.com/p/django-page-cms/source/detail?r=285) (Dec 17, 2008) ###

Renamed some templates tags to don't overlap with other Django apps, like django-treemenus.

| **old** | **new** |
|:--------|:--------|
| show\_menu | pages\_menu|
| show\_sub\_menu | pages\_sub\_menu |
| show\_admin\_menu | pages\_admin\_menu |

### [r261](https://code.google.com/p/django-page-cms/source/detail?r=261) (Dec 5, 2008) ###

The placeholder template tag doesn't return a `<div class="placeholder">[content]</div>` anymore. Please wrap the template tags yourself in HTML you require. The templates of the example project was changed to follow the changes.

### [r259](https://code.google.com/p/django-page-cms/source/detail?r=259) (Dec 5, 2008) ###

The placeholder template tag has been revamped to be a more flexible. The new syntax is a bit different and will break unless you change your existing templates.

The **old** syntax:

```
{% placeholder [name] [page] [widget] %}
```

The **new** syntax:

```
{% placeholder [name] %}
{% placeholder [name] parsed %}

{% placeholder [name] with [widget] %}
{% placeholder [name] with [widget] parsed %}

{% placeholder [name] on [page]  %}
{% placeholder [name] on [page] parsed %}
{% placeholder [name] on [page] with [widget] %}
{% placeholder [name] on [page] with [widget] parsed %}
```

The `page` and `widget` parameter are both optional now. If now `page` parameter is given it will automatically take the current page (by using the `current_page` context variable) to get the content of the placeholder.

**New:** If you pass the word "parsed" the content of the template will be evaluated as Django template code, within the current template context. Each placeholder with that has the "parsed" parameter will also have a note in the admin interface noting its ability to be evaluated as template.

**New:** You can now also use a variable name optionally that is automatically set in the context view with the content of the placeholder. The content will not be embedded in a `div` tag.

```
{% placeholder right-column parsed as right_column %}

..random content..

<div class="my_funky_column">{{ right_column }}</div>
```

### [r252](https://code.google.com/p/django-page-cms/source/detail?r=252) (Nov 28, 2008) ###

The `mptt` app is now **required** to be added to the `INSTALLED_APPS` setting.
Just make sure your settings.py looks like that:

```
INSTALLED_APPS = (
    ...
    'mptt',
    'tagging',
    'pages',
)
```

### [r238](https://code.google.com/p/django-page-cms/source/detail?r=238) (Nov 26, 2008) ###

Removed `blank` and `null` options on the `sites` field of the `Page` model to enforce validation. That's now mandatory given the new `CurrentSiteMiddleware`. Change your site objects to match your domain(s)!

No worries if you use different subdomains on the same Django instance, pages checks if the request host ends with one of the Site instances.

### [r224](https://code.google.com/p/django-page-cms/source/detail?r=224) (Nov 23, 2008) ###

Moved [example project](http://code.google.com/p/django-page-cms/source/browse/trunk#trunk/example) to its own subdirectory in the subversion root.

In case you updated from a previous version please make sure all remaining `*.pyc` files are deleted from your checkout before you run the example project again. On Linux/Unix systems that can be achieved by running the following command in the django-page-cms checkout directory:

```
find . -name '*.pyc' -exec rm {} \;
```

### [r222](https://code.google.com/p/django-page-cms/source/detail?r=222)/[r223](https://code.google.com/p/django-page-cms/source/detail?r=223) (Nov 23, 2008) ###

Added a CurrentSiteMiddleware middleware that is now mandatory. This enables django-page-cms to serve multiple domains without having to have multiple Django processes.

Please modify your settings to look like this:

```
MIDDLEWARE_CLASSES = (
    # ..
    'pages.middleware.CurrentSiteMiddleware',
)
```

### [r207](https://code.google.com/p/django-page-cms/source/detail?r=207) (Nov 18, 2008) ###

Added new DateTime field "publication\_end\_date" to Page model.

Use the following SQL statement as a helper if you need to modify existing data:

```
BEGIN;
ALTER TABLE pages_page
    ADD COLUMN publication_end_date datetime NULL;
COMMIT;
```