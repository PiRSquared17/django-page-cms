# FAQ #

## How can I specify a meta description for each page and for each language? ##

If you want to have a field for the description meta tag just add a placeholder in your template:

```
<meta name="keywords" content="{% placeholder meta_description with TextInput %}" />
```

And an translated field should appears in the admin.

## How can I show content part of the page without using a placeholder? ##

The show\_content template tags is here for that:

```
{% show_content the_page_object "the_content_type" %}
```

You can also specify the slug of the page instead of the page object itself:

```
{% show_content "my-page-slug" "the_content_type" %}
```

For a full documenation : [display content in templates](DisplayContentInTemplates.md)

## Nothing show up at the frontend. What is the problem? ##

  * Check that you have set your site domain name correctly (ie: for local-host development you will need to set it to 127.0.0.1:8000)
  * Check that you have published the page correctly

## The tree collapse and doesn't expand. What is the problem? ##

  * Check that you have set your site domain name correctly (ie: for local-host development you will need to set it to 127.0.0.1:8000, you use localhost:8000 you must have an entry called localhost:8000).

  * Check also that the SITE\_ID you have in your settings file is the one you are using to access.

## Add a language prefix before the urls ##

  1. change the url routing to accept a language prefix parameter (lang)
  1. the default view named "details" accept this parameter and display the page content accordingly.