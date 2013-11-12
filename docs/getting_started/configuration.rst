.. _configuration:

#############
Configuration
#############

django CMS has a number of settings to configure its behaviour. These should
be available in your ``settings.py`` file.

*****************
Required Settings
*****************

.. setting:: CMS_TEMPLATES

CMS_TEMPLATES
=============

Default: ``()`` (Not a valid setting!)

A list of templates you can select for a page.

Example::

    CMS_TEMPLATES = (
        ('base.html', gettext('default')),
        ('2col.html', gettext('2 Column')),
        ('3col.html', gettext('3 Column')),
        ('extra.html', gettext('Some extra fancy template')),
    )

.. note::

    All templates defined in :setting:`CMS_TEMPLATES` **must** contain at least
    the ``js`` and ``css`` sekizai namespaces. For more information, see
    :ref:`sekizai-namespaces`.

.. warning::

    django CMS requires some special templates to function correctly. These are
    provided within ``cms/templates/cms``. You are strongly advised not to use
    ``cms`` as a directory name for your own project templates.

*******************
Basic Customization
*******************

.. setting:: CMS_TEMPLATE_INHERITANCE

CMS_TEMPLATE_INHERITANCE
========================

Default: ``True``

Enables the inheritance of templates from parent pages.

When enabled, pages' ``Template`` options will include a new default: *Inherit
from the parent page* (unless the page is a root page).


.. setting:: CMS_PLACEHOLDER_CONF

CMS_PLACEHOLDER_CONF
====================

Default: ``{}``

Used to configure placeholders. If not given, all plugins will be available in
all placeholders.

Example::

    CMS_PLACEHOLDER_CONF = {
        'content': {
            'plugins': ['TextPlugin', 'PicturePlugin'],
            'text_only_plugins': ['LinkPlugin']
            'extra_context': {"width":640},
            'name': gettext("Content"),
            'language_fallback': True,
            'child_classes': {
                'TextPlugin': ['PicturePlugin', 'LinkPlugin'],
            },
            'parent_classes': {
                'LinkPlugin': ['TextPlugin', 'StackPlugin'],
            }
        },
        'right-column': {
            "plugins": ['TeaserPlugin', 'LinkPlugin'],
            "extra_context": {"width":280},
            'name': gettext("Right Column"),
            'limits': {
                'global': 2,
                'TeaserPlugin': 1,
                'LinkPlugin': 1,
            },
            'plugin_modules': {
                'LinkPlugin': 'Extra',
            }.
            'plugin_labels': {
                'LinkPlugin': 'Add a link',
            }.
        },
        'base.html content': {
            "plugins": ['TextPlugin', 'PicturePlugin', 'TeaserPlugin']
        },
    }

You can combine template names and placeholder names to granularly define
plugins, as shown above with ``base.html content``.

``plugins``
    A list of plugins that can be added to this placeholder. If not supplied,
    all plugins can be selected.

``text_only_plugins``
    A list of additional plugins available only in the TextPlugin, these
    plugins can't be added directly to this placeholder.

``extra_context``
    Extra context that plugins in this placeholder receive.

``name``
    The name displayed in the Django admin. With the gettext stub, the name can
    be internationalized.

``limits``
    Limit the number of plugins that can be placed inside this placeholder.
    Dictionary keys are plugin names and the values are their respective
    limits. Special case: ``global`` - Limit the absolute number of plugins in
    this placeholder regardless of type (takes precedence over the
    type-specific limits).

``language_fallback``
    When ``True``, if the placeholder has no plugin for the current language
    it falls back to the fallback languages as specified in :setting:`CMS_LANGUAGES`.
    Defaults to ``False`` to maintain pre-3.0 behavior.

``plugin_modules``
    A dictionary of plugins and custom module names to group plugin in the
    toolbar UI.

``plugin_labels``
    A dictionary of plugins and custom labels to show in the toolbar UI.

``child_classes``
    A dictionary of plugin names with lists describing which plugins may be
    placed inside each plugin. If not supplied, all plugins can be selected.

``parent_classes``
    A dictionary of plugin names with lists describing which plugins may contain
    each plugin. If not supplied, all plugins can be selected.


.. setting:: CMS_PLUGIN_CONTEXT_PROCESSORS

CMS_PLUGIN_CONTEXT_PROCESSORS
=============================

Default: ``[]``

A list of plugin context processors. Plugin context processors are callables
that modify all plugins' context *before* rendering. See
:doc:`../extending_cms/custom_plugins` for more information.

.. setting:: CMS_PLUGIN_PROCESSORS

CMS_PLUGIN_PROCESSORS
=====================

Default: ``[]``

A list of plugin processors. Plugin processors are callables that modify all
plugins' output *after* rendering. See :doc:`../extending_cms/custom_plugins`
for more information.

.. setting:: CMS_APPHOOKS

CMS_APPHOOKS
============

Default: ``()``

A list of import paths for :class:`cms.app_base.CMSApp` subclasses.

By default, apphooks are auto-discovered in applications listed in all
:setting:`django:INSTALLED_APPS`, by trying to import their ``cms_app`` module.

When ``CMS_APPHOOKS`` is set, auto-discovery is disabled.

Example::

    CMS_APPHOOKS = (
        'myapp.cms_app.MyApp',
        'otherapp.cms_app.MyFancyApp',
        'sampleapp.cms_app.SampleApp',
    )

********************
Editor configuration
********************

The Wymeditor from :mod:`cms.plugins.text` plugin can take the same
configuration as vanilla Wymeditor. Therefore you will need to learn 
how to configure that. The best thing to do is to head 
over to the `Wymeditor examples page 
<http://files.wymeditor.org/wymeditor-1.0.0b2/examples/>`_
in order to understand how Wymeditor works. 

The :mod:`cms.plugins.text` plugin exposes several variables named
WYM_* that correspond to the wym configuration. The simplest 
way to get started with this is to go to ``cms/plugins/text/settings.py``
and copy over the WYM_* variables and you will realize they 
match one to one to Wymeditor's.

Currently the following variables are available:

* ``WYM_TOOLS``
* ``WYM_CONTAINERS``
* ``WYM_CLASSES``
* ``WYM_STYLES``
* ``WYM_STYLESHEET``

*************
I18N and L10N
*************

.. setting:: CMS_LANGUAGES

CMS_LANGUAGES
=============

Default: Value of :setting:`django:LANGUAGES` converted to this format

Defines the languages available in django CMS.

Example::

    CMS_LANGUAGES = {
        1: [
            {
                'code': 'en',
                'name': gettext('English'),
                'fallbacks': ['de', 'fr'],
                'public': True,
                'hide_untranslated': True,
                'redirect_on_fallback':False,
            },
            {
                'code': 'de',
                'name': gettext('Deutsch'),
                'fallbacks': ['en', 'fr'],
                'public': True,
            },
            {
                'code': 'fr',
                'name': gettext('French'),
                'public': False,
            },
        ],
        2: [
            {
                'code': 'nl',
                'name': gettext('Dutch'),
                'public': True,
                'fallbacks': ['en'],
            },
        ],
        'default': {
            'fallbacks': ['en', 'de', 'fr'],
            'redirect_on_fallback':True,
            'public': True,
            'hide_untranslated': False,
        }
    }

.. note:: Make sure you only define languages which are also in :setting:`django:LANGUAGES`.

.. warning::

    Make sure you use **language codes** (`en-us`) and not **locale names**
    (`en_US`) here and in :setting:`django:LANGUAGES`.
    Use :ref:`check command <cms-check-command>` to check for correct syntax.

``CMS_LANGUAGES`` has different options where you can define how different
languages behave, with granular control.

On the first level you can set values for each ``SITE_ID``. In the example
above we define two sites. The first site has 3 languages (English, German and
French) and the second site has only Dutch.

The ``default`` node defines default behavior for all languages. You can
overwrite the default settings with language-specific properties. For example
we define ``hide_untranslated`` as ``False`` globally, but the English language
overwrites this behavior.

Every language node needs at least a ``code`` and a ``name`` property. ``code``
is the ISO 2 code for the language, and ``name`` is the verbose name of the
language.

.. note:: 

    With a gettext() lambda function you can make language names translatable.
    To enable this add ``gettext = lambda s: s`` at the beginning of your
    settings file.

What are the properties a language node can have?

.. setting::code

code
----
String. RFC5646 code of the language.

Example: ``"en"``.

.. note:: Is required for every language.

name
----
String. The verbose name of the language.

.. note:: Is required for every language.

.. setting::public

public
------
Determines whether this language accessible in the frontend. You may want for example to keep a langage private until your content has been fully translated.

Type: Boolean
Default: ``True``

.. setting::fallbacks

fallbacks
---------
A list of alternative languages, in order of preference, that are to be used if
a page is not translated yet..

Example: ``['de', 'fr']``
Default: ``[]``

.. setting::hide_untranslated

hide_untranslated
-----------------
Hide untranslated pages in menus

Type: Boolean
Default: ``True``

.. setting::redirect_on_fallback

redirect_on_fallback
--------------------
Determines behaviour when the preferred language is not available. If ``True``,
will redirect to the URL of the same page in the fallback language. If
``False``, the content will be displayed in the fallback language, but there
will be no redirect.

Type: Boolean
Default:``True``


Unicode support for automated slugs
===================================

django CMS supports automated slug generation from page titles that contain
unicode characters via the unihandecode.js project. To enable support for
unihandecode.js, at least :setting:`CMS_UNIHANDECODE_HOST` and
:setting:`CMS_UNIHANDECODE_VERSION` must be set.


.. setting:: CMS_UNIHANDECODE_HOST

CMS_UNIHANDECODE_HOST
---------------------

default: ``None``

Must be set to the URL where you host your unihandecode.js files. For licensing
reasons, django CMS does not include unihandecode.js.

If set to ``None``, the default, unihandecode.js is not used.


.. note::

    Unihandecode.js is a rather large library, especially when loading support
    for Japanese. It is therefore very important that you serve it from a
    server that supports gzip compression. Further, make sure that those files
    can be cached by the browser for a very long period.


.. setting:: CMS_UNIHANDECODE_VERSION

CMS_UNIHANDECODE_VERSION
------------------------

default: ``None``

Must be set to the version number (eg ``'1.0.0'``) you want to use. Together
with :setting:`CMS_UNIHANDECODE_HOST` this setting is used to build the full
URLs for the javascript files. URLs are built like this:
``<CMS_UNIHANDECODE_HOST>-<CMS_UNIHANDECODE_VERSION>.<DECODER>.min.js``.


.. setting:: CMS_UNIHANDECODE_DECODERS

CMS_UNIHANDECODE_DECODERS
-------------------------

default: ``['ja', 'zh', 'vn', 'kr', 'diacritic']``

If you add additional decoders to your :setting:`CMS_UNIHANDECODE_HOST``, you can add them to this setting.


.. setting:: CMS_UNIHANDECODE_DEFAULT_DECODER

CMS_UNIHANDECODE_DEFAULT_DECODER
--------------------------------

default: ``'diacritic'``

The default decoder to use when unihandecode.js support is enabled, but the
current language does not provide a specific decoder in
:setting:`CMS_UNIHANDECODE_DECODERS`. If set to ``None``, failing to find a
specific decoder will disable unihandecode.js for this language.


**************
Media Settings
**************

.. setting:: CMS_MEDIA_PATH

CMS_MEDIA_PATH
==============

default: ``cms/``

The path from :setting:`django:MEDIA_ROOT` to the media files located in ``cms/media/``

.. setting:: CMS_MEDIA_ROOT

CMS_MEDIA_ROOT
==============

Default: :setting:`django:MEDIA_ROOT` + :setting:`CMS_MEDIA_PATH`

The path to the media root of the cms media files.

.. setting:: CMS_MEDIA_URL

CMS_MEDIA_URL
=============

default: :setting:`django:MEDIA_URL` + :setting:`CMS_MEDIA_PATH`

The location of the media files that are located in ``cms/media/cms/``

.. setting:: CMS_PAGE_MEDIA_PATH

CMS_PAGE_MEDIA_PATH
===================

Default: ``'cms_page_media/'``

By default, django CMS creates a folder called ``cms_page_media`` in your
static files folder where all uploaded media files are stored. The media files
are stored in subfolders numbered with the id of the page.

You need to ensure that the directory to which it points is writable by the
user under which Django will be running.


****
URLs
****

*****************
Advanced Settings
*****************

.. setting:: CMS_PERMISSION

CMS_PERMISSION
==============

Default: ``False``

When enabled, 3 new models are provided in Admin:

- Pages global permissions
- User groups - page
- Users - page

In the edit-view of the pages you can now assign users to pages and grant them
permissions. In the global permissions you can set the permissions for users
globally.

If a user has the right to create new users he can now do so in the "Users -
page", but he will only see the users he created. The users he created can also
only inherit the rights he has. So if he only has been granted the right to
edit a certain page all users he creates can, in turn, only edit this page.
Naturally he can limit the rights of the users he creates even further,
allowing them to see only a subset of the pages to which he is allowed access.

.. setting:: CMS_RAW_ID_USERS

CMS_RAW_ID_USERS
================

Default: ``False``

This setting only applies if :setting:`CMS_PERMISSION` is ``True``

The ``view restrictions`` and ``page permissions`` inlines on the
:class:`cms.models.Page` admin change forms can cause performance problems
where there are many thousands of users being put into simple select boxes. If
set to a positive integer, this setting forces the inlines on that page to use
standard Django admin raw ID widgets rather than select boxes if the number of
users in the system is greater than that number, dramatically improving
performance.

.. note:: Using raw ID fields in combination with ``limit_choices_to`` causes
          errors due to excessively long URLs if you have many thousands of
          users (the PKs are all included in the URL of the popup window). For
          this reason, we only apply this limit if the number of users is
          relatively small (fewer than 500). If the number of users we need to
          limit to is greater than that, we use the usual input field instead
          unless the user is a CMS superuser, in which case we bypass the
          limit.  Unfortunately, this means that non-superusers won't see any
          benefit from this setting.

.. setting:: CMS_PUBLIC_FOR

CMS_PUBLIC_FOR
==============

Default: ``all``

Determines whether pages without any view restrictions are public by default or
staff only. Possible values are ``all`` and ``staff``.

.. setting:: CMS_CACHE_DURATIONS

CMS_CACHE_DURATIONS
===================

This dictionary carries the various cache duration settings.

``'content'``
-------------

Default: ``60``

Cache expiration (in seconds) for :ttag:`show_placeholder` and :ttag:`page_url`
template tags.

.. note::

    This settings was previously called :setting:`CMS_CONTENT_CACHE_DURATION`

``'menus'``
-----------

Default: ``3600``

Cache expiration (in seconds) for the menu tree.

.. note::

    This settings was previously called :setting:`MENU_CACHE_DURATION`

``'permissions'``
-----------------

Default: ``3600``

Cache expiration (in seconds) for view and other permissions.

.. setting:: CMS_CACHE_PREFIX

CMS_CACHE_PREFIX
================

Default: ``cms-``


The CMS will prepend the value associated with this key to every cache access
(set and get). This is useful when you have several django CMS installations,
and you don't want them to share cache objects.

Example::

    CMS_CACHE_PREFIX = 'mysite-live'

.. note::

    Django 1.3 introduced a site-wide cache key prefix. See Django's own docs
    on :ref:`cache key prefixing <django:cache_key_prefixing>`


.. setting::CMS_MAX_PAGE_PUBLISH_REVERSIONS

CMS_MAX_PAGE_PUBLISH_REVERSIONS
===============================

Default: ``25``

If `django-reversion`_ is installed everything you do with a page and all
plugin changes will be saved in a revision. 

In the page admin there is a ``History`` button to revert to previous version
of a page. In the past, databases using django-reversion could grow huge. To
help address this issue, only *published* revisions will now be saved.

This setting declares how many published revisions are saved in the database.
By default the newest 25 published revisions are kept; all others are deleted
when you publish a page.

If set to *0* all published revisions are kept, but you will need to ensure
that the revision table does not grow excessively large.


.. setting:: CMS_TOOLBARS

CMS_TOOLBARS
============

Default: ``None``

If defined, specifies the list of toolbar modifiers to be used to populate the
toolbar as import paths.


.. _django-reversion: https://github.com/etianen/django-reversion
.. _unihandecode.js: https://github.com/ojii/unihandecode.js

