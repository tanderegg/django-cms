#####################
Extending the Toolbar
#####################

.. versionadded:: 3.0

You can add and remove items to the toolbar. This allows you to integrate your
application in the frontend editing mode of django CMS and provide your users
with a streamlined editing experience.

For the toolbar API reference, please refer to :ref:`toolbar-api-reference`.


***********
Registering
***********

There are two ways to control what gets shown in the toolbar. 

One is the :setting:`CMS_TOOLBARS`. This gives you full control over which
classes are loaded, but requires that you specify them all manually.

The other is to provide ``cms_toolbar.py`` files in your apps, which will be
automatically loaded as long :setting:`CMS_TOOLBARS` is not set (or set to
``None``).

If you use the automated way, your ``cms_toolbar.py`` file should contain
classes that extend from ``cms.toolbar_base.CMSToolbar`` and are registered using :meth:`cms.toolbar_pool.toolbar_pool.register`.
The register function can be used as a decorator.

These have four attributes:
* toolbar (the toolbar object)
* request (the current request)
* is_current_app (a flag indicating whether the current request is handled by the same app as the function is in)
* app_path (the name of the app used for the current request)

This classes must implement a ``populate`` or ``post_template_populate`` function. An optional ``request_hook`` function
is available for overwrite as well.

* The populate functions will only be called if the current user is a staff user.
* The ``populate`` function will be called before the template and plugins are rendered.
* The ``post_template_populate`` function will be called after the template is rendered.
* The ``request_hook`` function is called before the view and may return a response. This way you would be able to issue
  redirects from a toolbar if needed

A simple example, registering a class that does nothing::

    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class MoopModifier(CMSToolbar):

        def populate(self):
            pass

        def post_template_populate(self):
            pass

        def request_hook(self):
            pass


.. warning::

    ``post_template_populate`` maybe finds different nodes in the toolbar than propagate.

.. tip::

    You can change the toolbar or add items inside a plugin render method (context['request'].toolbar) or inside a view
    (request.toolbar)

************
Adding items
************

Items can be added through the various :ref:`APIs <toolbar-api-reference>`
exposed by the toolbar and its items. 

To add a :class:`cms.toolbar.items.Menu` to the toolbar, use
:meth:`cms.toolbar.toolbar.CMSToolbar.get_or_create_menu` which will either add a menu if
it doesn't exist, or create it. 

Then, to add a link to your changelist that will open in the sideframe, use the
:meth:`cms.toolbar.items.ToolbarMixin.add_sideframe_item` method on the menu
object returned.

When adding items, all arguments other than the name or identifier should be
given as **keyword arguments**. This will help ensure that your custom toolbar
items survive upgrades.

Following our :doc:`extending_examples`, let's add the poll app
to the toolbar::

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class PollToolbar(CMSToolbar):

        def populate(self):
            if self.is_current_app:
                menu = self.toolbar.get_or_create_menu('poll-app', _('Polls'))
                url = reverse('admin:polls_poll_changelist')
                menu.add_sideframe_item(_('Poll overview'), url=url)


However, there's already a menu added by the CMS which provides access to
various admin views, so you might want to add your menu as a sub menu there.
To do this, you can use positional insertion coupled with the fact that
:meth:`cms.toolbar.toolbar.CMSToolbar.get_or_create_menu` will return already existing
menus::


    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar.items import Break
    from cms.cms_toolbar import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class PollToolbar(CMSToolbar):

        def populate(self):
            admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, _('Site'))
            position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)
            menu = admin_menu.get_or_create_menu('poll-menu', _('Polls'), position=position)
            url = reverse('admin:polls_poll_changelist')
            menu.add_sideframe_item(_('Poll overview'), url=url)
            admin_menu.add_break('poll-break', position=menu)


===========================
Adding Items Alphabetically
===========================

Sometimes it is desireable to add sub-menus from different applications
alphabetically. This can be challenging due to the non-obvious manner in which
your apps will be loaded into Django and is further complicated when you add new
applications over time.

To aide developers, django-cms exposes a :meth:`cms.toolbar.items.ToolbarMixin.get_alphabetical_insert_position`
method, which, if used consistently can produce alphabetized sub-menus, even
when they come from multiple applications.

An example is shown here for an 'Offices' app, which allows handy access to
certain admin functions for managing office locations in a project::

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_base import CMSToolbar
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar.items import Break, SubMenu
    from cms.cms_toolbar import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK

    @toolbar_pool.register
    class OfficesToolbar(CMSToolbar):

        def populate(self):
            #
            # 'Apps' is the spot on the existing djang-cms toolbar admin_menu
            # 'where we'll insert all of our applications' menus.
            #
            admin_menu = self.toolbar.get_or_create_menu(
                ADMIN_MENU_IDENTIFIER, _('Apps')
            )

            #
            # Let's check to see where we would insert an 'Offices' menu in the
            # admin_menu.
            #
            position = admin_menu.get_alphabetical_insert_position(
                _('Offices'),
                SubMenu
            )

            #
            # If zero was returned, then we know we're the first of our
            # applications' menus to be inserted into the admin_menu, so, here
            # we'll compute that we need to go after the first
            # ADMINISTRATION_BREAK and, we'll insert our own break after our
            # section.
            #
            if not position:
                # OK, use the ADMINISTRATION_BREAK location + 1
                position = admin_menu.find_first(
                    Break,
                    identifier=ADMINISTRATION_BREAK
                ) + 1
                # Insert our own menu-break, at this new position. We'll insert
                # all subsequent menus before this, so it will ultimately come
                # after all of our applications' menus.
                admin_menu.add_break('custom-break', position=position)

            # OK, create our office menu here.
            office_menu = admin_menu.get_or_create_menu(
                'offices-menu',
                _('Offices ...'),
                position=position
            )

            # Let's add some sub-menus to our office menu that help our users
            # manage office-related things.

            # Take the user to the admin-listing for offices...
            url = reverse('admin:offices_office_changelist')
            office_menu.add_sideframe_item(_('Offices List'), url=url)

            # Display a modal dialogue for creating a new office...
            url = reverse('admin:offices_office_add')
            office_menu.add_modal_item(_('Add New Office'), url=url)

            # Add a break in the submenus
            office_menu.add_break()

            # More submenus...
            url = reverse('admin:offices_state_changelist')
            office_menu.add_sideframe_item(_('States List'), url=url)

            url = reverse('admin:offices_state_add')
            office_menu.add_modal_item(_('Add New State'), url=url)

Here is the resulting toolbar (with a few other menus sorted alphabetically
beside it)

|alphabetized-toolbar-app-menus|

.. |alphabetized-toolbar-app-menus| image:: ../images/alphabetized-toolbar-app-menus.png

==========================
Adding items through views
==========================
Another way to add items to the toolbar is through our own views (``polls/views.py``).
This method can be useful if you need to access certain variables, in our case e.g. the
selected poll and its sub-methods::

    from django.core.urlresolvers import reverse
    from django.shortcuts import get_object_or_404, render
    from django.utils.translation import ugettext_lazy as _

    from polls.models import Poll


    def detail(request, poll_id):
        poll = get_object_or_404(Poll, pk=poll_id)
        menu = request.toolbar.get_or_create_menu('polls-app', _('Polls'))
        menu.add_modal_item(_('Change this Poll'), url=reverse('admin:polls_poll_change', args=[poll_id]))
        menu.add_sideframe_item(_('Show History of this Poll'), url=reverse('admin:polls_poll_history', args=[poll_id]))
        menu.add_sideframe_item(_('Delete this Poll'), url=reverse('admin:polls_poll_delete', args=[poll_id]))

        return render(request, 'polls/detail.html', {'poll': poll})
