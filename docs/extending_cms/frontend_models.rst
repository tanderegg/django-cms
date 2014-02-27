.. _frontend-editable-fields:

###########################################
Frontend editing for Page and Django models
###########################################

.. versionadded:: 3.0

django CMS frontend editing can also be used to edit non-placeholder fields from
the frontend, both for pages and your standard Django models.

Using this interface, you can double click on a value of a model instance in
the frontend and access the instance changeform in a popup window, like the page
changeform.


.. warning::

    Templatetag used by this feature mark as safe the content of the rendered
    model attribute. This may be a security risk if used on fields which may
    hold non-trusted content. Be aware, and use the templatetags accordingly.


.. warning::

    This feature is only partially compatible with django-hvad: using
    ``render_model`` with hvad-translated fields (say
    {% render_model object 'translated_field' %} return error if the
    hvad-enabled object does not exists in the current language.
    As a workaround ``render_model_icon`` can be used instead.

************
Templatetags
************

This feature relies on four templatetag sharing common code:

* :ttag:`render_model`
* :ttag:`render_model_icon`
* :ttag:`render_model_add`
* :ttag:`render_model_block`

Look at the tag-specific page for a detailed reference; in the examples
below ``render_model`` is assumed.


****************
Page titles edit
****************

For CMS pages you can edit the titles from the frontend; according to the
attribute specified a overridable default field will be editable.

Main title::

    {% render_model request.current_page "title" %}


Page title::

    {% render_model request.current_page "page_title" %}

Menu title::

    {% render_model request.current_page "menu_title" %}

All three titles::

    {% render_model request.current_page "titles" %}


You can always customize the editable fields by providing the
`edit_field` parameter::

    {% render_model request.current_page "title" "page_title,menu_title" %}


**************
Page menu edit
**************

By using the special keyword ``changelist`` as edit field the frontend
editing will show the page tree; a common pattern for this is to enable
changes in the menu by wrapping the menu templatetags:

.. code-block:: html+django

    {% render_model_block request.current_page "changelist" %}
        <h3>Menu</h3>
        <ul>
            {% show_menu 1 100 0 1 "sidebar_submenu_root.html" %}
        </ul>
    {% endrender_model_block %}

Will render to:

.. code-block:: html+django

    <div class="cms_plugin cms_plugin-cms-page-changelist-1">
        <h3>Menu</h3>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/another">another</a></li>
            [...]
    </div>
    
.. warning:
    
    Be aware that depending on the layout of your menu templates, clickable
    area of the menu may completely overlap with the active area of the
    frontend editor thus preventing editing. In this case you may use
    ``{% render_model_icon %}``.
    The same conflict exists when menu template is managed by a plugin.

******************
Django models edit
******************

For Django models you can further customize what's editable on the frontend
and the resulting forms.

Complete changeform edit
========================

You need to properly setup your admin class by adding the ``FrontendEditableAdminMixin``
mixin to the parents of your admin class (see
:mod:`Django admin documentation <django.contrib.admin>` for further information)
on Django admin::

    from cms.admin.placeholderadmin import FrontendEditableAdminMixin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
        ...

Then setup the templates adding ``render_model`` templatetag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" %}</h1>
    {% endblock content %}

See :ttag:`templatetag reference <render_model>` for arguments documentation.


Selected fields edit
====================

Frontend editing is also possible for a set of fields.

Set up the admin
----------------

You need to add to your model admin a tuple of fields editable from the frontend
admin::

    from cms.admin.placeholderadmin import FrontendEditableAdminMixin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
        frontend_editable_fields = ("foo", "bar")
        ...

Set up the template
-------------------

Then add comma separated list of fields (or just the name of one field) to
the templatetag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" %}</h1>
    {% endblock content %}



Special attributes
==================

The ``attribute`` argument of the templatetag is not required to be a model field,
property or method can also be used as target; in case of a method, it will be
called with request as argument.


.. _custom-views:

Custom views
============

You can link any field to a custom view (not necessarily an admin view) to handle
model-specific editing workflow.

The custom view can be passed either as a named url (``view_url`` parameter)
or as name of a method (or property) on the instance being edited
(``view_method`` parameter).
In case you provide ``view_method`` it will be called whenever the templatetag is
evaluated with ``request`` as parameter.

The custom view does not need to obey any specific interface; it will get
``edit_fields`` value as a ``GET`` parameter.

See :ttag:`templatetag reference <render_model>` for arguments documentation.

Example ``view_url``::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" "" "admin:exampleapp_example1_some_view" %}</h1>
    {% endblock content %}


Example ``view_method``::
    
    class MyModel(models.Model):
        char = models.CharField(max_length=10)
        
        def some_method(self, request):
            return "/some/url"
    

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" "" "" "some_method" %}</h1>
    {% endblock content %}


Model changelist
================

By using the special keyword ``changelist`` as edit field the frontend
editing will show the model changelist:

.. code-block:: html+django

    {% render_model instance "name" "changelist" %}

Will render to:

.. code-block:: html+django

    <div class="cms_plugin cms_plugin-myapp-mymodel-changelist-1">
        My Model Instance Name
    </div>


.. filters:

*******
Filters
*******

If you need to apply filters to the output value of the templatetag, add quoted
sequence of filters as in Django :ttag:`django:filter` templatetag:

.. code-block:: html+django

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "attribute" "" "" "truncatechars:9" %}</h1>
    {% endblock content %}



****************
Context variable
****************

The templatetag output can be saved in a context variable for later use, using
the standard `as` syntax:

.. code-block:: html+django

    {% load cms_tags %}

    {% block content %}
    {% render_model instance "attribute" as variable %}

    <h1>{{ variable }}</h1>

    {% endblock content %}

