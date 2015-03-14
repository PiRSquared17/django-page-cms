The **pagelink** system permit to add **internal link** in a CMS content using the WYMEditor placeholder by a customised dialog (button).

In the background the logic implemented accomplish 2 things:

  1. Maintaining the correct absolute URL of each link if a page is moved over the tree
  1. Inform the admin if a page has a broken URL after the linked page is removed.

## How this work ##

All **page links** added with the custom WYMEditor dialog is formated like this:
```
<a class="page_ID" href="/pages/page-test/">Text selected</a>
```

Then when the page is displayed:
  * All links found with the class 'page\_ID' have the URLS updated live.
  * If a link point to a non existing page a message is sent to the admin to notifify the     editor that there is a broken link in this page.
```
<a class="pagelink_broken" href="/pages/page-test/" title="Page Test">Text selected</a>
```

This functionality is only available with the WYMEditor placeholder content for now.

## To enable ''pagelink'' system ##

Add in your project settings.py file:
```
PAGE_LINK_FILTER = True
```

Now when you use a WYEditor placeholder the Rich Text Editor offer a new button for adding **internal page** links!

## TODO ##

  * Optimize the page list on WyMEditor popup with cache logic.