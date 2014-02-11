#################
Plugins reference
#################

.. :module:: cms.plugins.file

.. :class:: cms.plugins.file.models.FilePlugin

****
File
****

Allows you to upload a file. A filetype icon will be assigned based on the file
extension.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.file',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

You might consider using `django-filer`_ with `django CMS plugin`_ and its
``cmsplugin_filer_file`` component instead.

.. warning::

    The builtin file plugin only works with local storages. If you need
    more advanced solutions, please look at alternative file plugins for the
    django CMS, such as `django-filer`_.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.flash

.. :class:: cms.plugins.flash.cms_plugins.FlashPlugin

*****
Flash
*****

Allows you to upload and display a Flash SWF file on your page.

For installation be sure you have the following in the
:setting:`django:INSTALLED_APPS` setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.flash',
        # ...
    )

.. :module:: cms.plugins.googlemap

.. :class:: cms.plugins.googlemap.cms_plugins.GoogleMapPlugin

*********
GoogleMap
*********

Displays a map of an address on your page.

Both address and coordinates are supported to center the map; zoom level and
route planner can be set when adding/editing plugin in the admin.

.. versionadded:: 2.3.2
    width/height parameter has been added, so it's no longer required to set
    plugin container size in CSS or template.

.. versionchanged:: 2.3.2
    Zoom level is set via a select field which ensure only legal values are used.

.. note:: Due to the above change, `level` field is now marked as `NOT NULL`,
    and a datamigration has been introduced to modify existing googlemap plugin
    instance to set the default value if `level` if is `NULL`.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.googlemap',
        # ...
    )


.. :module:: cms.plugins.picture

.. :class:: cms.plugins.picture.cms_plugins.PicturePlugin

*******
Picture
*******

Displays a picture in a page.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.picture',
        # ...
    )

There are several solutions for Python and Django out there to automatically
resize your pictures, you can find some on `Django Packages`_ and compare them
there.

In your project template directory create a folder called ``cms/plugins`` and
in it create a file called ``picture.html``. Here is an example
``picture.html`` template using `easy-thumbnails`_:

.. code-block:: html+django

    {% load thumbnail %}

    {% if link %}<a href="{{ link }}">{% endif %}
    {% if placeholder == "content" %}
        <img src="{% thumbnail picture.image 300x600 %}"{% if picture.alt %} alt="{{ picture.alt }}"{% endif %} />
    {% else %}
        {% if placeholder == "teaser" %}
            <img src="{% thumbnail picture.image 150x150 %}"{% if picture.alt %} alt="{{ picture.alt }}"{% endif %} />
        {% endif %}
    {% endif %}
    {% if link %}</a>{% endif %}


In this template the picture is scaled differently based on which placeholder
it was placed in.

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

.. note:: In order to improve clarity, some Picture fields have been omitted in
          the example template code.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_image`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

******
Teaser
******

Displays a teaser box for another page or a URL. A picture and a description
can be added.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
settings in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.teaser',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_teaser`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

****
Text
****

Consider using `djangocms-text-ckeditor
<https://github.com/divio/djangocms-text-ckeditor>`_ for displaying text. You
may of course use your preferred editor; others are available.

.. :module:: cms.plugins.video

.. :class:: cms.plugins.video.cms_plugins.VideoPlugin

*****
Video
*****

Plays Video Files or Youtube / Vimeo Videos. Uses the `OSFlashVideoPlayer
<http://github.com/FlashJunior/OSFlashVideoPlayer>`_. When uploading videos use either
.flv files or h264 encoded video files.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.video',
        # ...
    )

There are some settings you can set in your settings.py to overwrite some
default behavior:

* ``VIDEO_AUTOPLAY`` ((default: ``False``)
* ``VIDEO_AUTOHIDE`` (default: ``False``)
* ``VIDEO_FULLSCREEN`` (default: ``True``)
* ``VIDEO_LOOP`` (default: ``False``)
* ``VIDEO_AUTOPLAY`` (default: ``False``)
* ``VIDEO_BG_COLOR`` (default: ``"000000"``)
* ``VIDEO_TEXT_COLOR`` (default: ``"FFFFFF"``)
* ``VIDEO_SEEKBAR_COLOR`` (default: ``"13ABEC"``)
* ``VIDEO_SEEKBARBG_COLOR`` (default: ``"333333"``)
* ``VIDEO_LOADINGBAR_COLOR`` (default: ``"828282"``)
* ``VIDEO_BUTTON_OUT_COLOR`` (default: ``"333333"``)
* ``VIDEO_BUTTON_OVER_COLOR`` (default: ``"000000"``)
* ``VIDEO_BUTTON_HIGHLIGHT_COLOR`` (default: ``"FFFFFF"``)

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_video`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.twitter

.. :class:: cms.plugins.twitter.cms_plugins.TwitterRecentEntriesPlugin

.. :class:: cms.plugins.twitter.cms_plugins.TwitterSearchPlugin

*******
Twitter
*******

Twitter disabled V1 of their API, thus we've removed the twitter plugin
(``cms.plugins.twitter``).

For alternatives have a look at these plugins:

* https://github.com/nephila/djangocms_twitter
* https://github.com/changer/cmsplugin-twitter

.. :module:: cms.plugins.inherit

.. :class:: cms.plugins.twitter.cms_plugins.InheritPagePlaceholderPlugin

*******
Inherit
*******

Displays all plugins of another page or another language. Great if you always
need the same plugins on a lot of pages.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.inherit',
        # ...
    )

.. warning:: The inherit plugin is currently the only core-plugin which
             **cannot** be used in non-cms placeholders.

.. _Django Packages: http://djangopackages.com/grids/g/thumbnails/
.. _easy-thumbnails: https://github.com/SmileyChris/easy-thumbnails
