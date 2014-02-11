# -*- coding: utf-8 -*-

from django.db.models import signals
import warnings
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.plugin_base import CMSPluginBase
from cms.models import CMSPlugin
from cms.utils.django_load import load, get_subclasses
from cms.utils.helpers import reversion_register
from cms.utils.placeholder import get_placeholder_conf
from cms.utils.compat.dj import force_unicode
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import url, patterns, include
from django.contrib.formtools.wizard.views import normalize_name
from django.db import connection
from django.db.models.fields.related import ManyToManyField, ReverseManyRelatedObjectsDescriptor
from django.template.defaultfilters import slugify
from django.utils.translation import get_language, deactivate_all, activate


class PluginPool(object):
    def __init__(self):
        self.plugins = {}
        self.discovered = False
        self.patched = False

    def discover_plugins(self):
        if self.discovered:
            return
        self.discovered = True
        load('cms_plugins')

    def register_plugin(self, plugin):
        """
        Registers the given plugin(s).

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if not issubclass(plugin, CMSPluginBase):
            raise ImproperlyConfigured(
                "CMS Plugins must be subclasses of CMSPluginBase, %r is not."
                % plugin
            )
        plugin_name = plugin.__name__
        if plugin_name in self.plugins:
            raise PluginAlreadyRegistered(
                "Cannot register %r, a plugin with this name (%r) is already "
                "registered." % (plugin, plugin_name)
            )

        plugin.value = plugin_name
        self.plugins[plugin_name] = plugin
        from cms.signals import pre_save_plugins, post_delete_plugins, pre_delete_plugins

        signals.pre_save.connect(pre_save_plugins, sender=plugin.model,
                                 dispatch_uid='cms_pre_save_plugin_%s' % plugin_name)
        signals.post_delete.connect(post_delete_plugins, sender=CMSPlugin,
                                    dispatch_uid='cms_post_delete_plugin_%s' % plugin_name)
        signals.pre_delete.connect(pre_delete_plugins, sender=CMSPlugin,
                                   dispatch_uid='cms_pre_delete_plugin_%s' % plugin_name)
        if 'reversion' in settings.INSTALLED_APPS:
            try:
                from reversion.registration import RegistrationError
            except ImportError:
                from reversion.revisions import RegistrationError
            try:
                reversion_register(plugin.model)
            except RegistrationError:
                pass

    def unregister_plugin(self, plugin):
        """
        Unregisters the given plugin(s).

        If a plugin isn't already registered, this will raise PluginNotRegistered.
        """
        plugin_name = plugin.__name__
        if plugin_name not in self.plugins:
            raise PluginNotRegistered(
                'The plugin %r is not registered' % plugin
            )
        del self.plugins[plugin_name]

    def set_plugin_meta(self):
        """
        Patches a plugin model by forcing a specifc db_table whether the
        'new style' table name exists or not. The same goes for all the
        ManyToMany attributes.
        This method must be run whenever a plugin model is accessed
        directly.

        The model is modified in place; a 'patched' attribute is added
        to the model to check whether it's already been modified.
        """
        if self.patched:
            return
        table_names = connection.introspection.table_names()
        subs = get_subclasses(CMSPlugin)
        for model in subs:
            if not model._meta.abstract:

                splitter = '%s_' % model._meta.app_label
                table_name = model._meta.db_table
                if (table_name not in table_names
                and splitter in table_name):
                    old_db_name = table_name
                    splitted = table_name.split(splitter, 1)
                    table_name = 'cmsplugin_%s' % splitted[1]
                    if table_name in table_names:
                        model._meta.db_table = table_name
                        warnings.warn(
                            'please rename the table "%s" to "%s" in %s\nThe compatibility code will be removed in 3.1' % (
                                table_name, old_db_name, model._meta.app_label), DeprecationWarning)
                for att_name in model.__dict__.keys():
                    att = model.__dict__[att_name]
                    if isinstance(att, ManyToManyField):
                        table_name = att.rel.through._meta.db_table
                        if (table_name not in table_names
                        and splitter in table_name):
                            old_db_name = table_name
                            table_name.split(splitter, 1)
                            table_name = 'cmsplugin_%s' % splitted[1]
                            if table_name in table_names:
                                att.rel.through._meta.db_table = table_name
                                warnings.warn(
                                    'please rename the table "%s" to "%s" in %s\nThe compatibility code will be removed in 3.1' % (
                                        table_name, old_db_name, model._meta.app_label), DeprecationWarning)
                    elif isinstance(att, ReverseManyRelatedObjectsDescriptor):
                        table_name = att.through._meta.db_table
                        if (table_name not in table_names
                        and splitter in table_name):
                            old_db_name = table_name
                            table_name.split(splitter, 1)
                            table_name = 'cmsplugin_%s_items' % splitted[1]
                            if table_name in table_names:
                                att.through._meta.db_table = table_name
                                warnings.warn(
                                    'please rename the table "%s" to "%s" in %s\nThe compatibility code will be removed in 3.1' % (
                                        table_name, old_db_name, model._meta.app_label), DeprecationWarning)

        self.patched = True

    def get_all_plugins(self, placeholder=None, page=None, setting_key="plugins", include_page_only=True):
        self.discover_plugins()
        self.set_plugin_meta()
        plugins = list(self.plugins.values())
        plugins.sort(key=lambda obj: force_unicode(obj.name))
        final_plugins = []
        if page:
            template = page.get_template()
        else:
            template = None
        allowed_plugins = get_placeholder_conf(
            setting_key,
            placeholder,
            template,
        )
        for plugin in plugins:
            include_plugin = False
            if placeholder:
                if plugin.require_parent:
                    include_plugin = False
                elif allowed_plugins:
                    if plugin.__name__ in allowed_plugins:
                        include_plugin = True
                elif setting_key == "plugins":
                    include_plugin = True
            if plugin.page_only and not include_page_only:
                include_plugin = False
            if include_plugin:
                final_plugins.append(plugin)

        if final_plugins:
            plugins = final_plugins

        # plugins sorted by modules
        plugins = sorted(plugins, key=lambda obj: force_unicode(obj.module))
        return plugins

    def get_text_enabled_plugins(self, placeholder, page):
        plugins = self.get_all_plugins(placeholder, page)
        plugins += self.get_all_plugins(placeholder, page, 'text_only_plugins')
        final = []
        for plugin in plugins:
            if plugin.text_enabled:
                if plugin not in final:
                    final.append(plugin)
        return final

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        self.discover_plugins()
        self.set_plugin_meta()
        return self.plugins[name]

    def get_patterns(self):
        self.discover_plugins()

        # We want untranslated name of the plugin for its slug so we deactivate translation
        lang = get_language()
        deactivate_all()

        try:
            url_patterns = []
            for plugin in self.get_all_plugins():
                p = plugin()
                slug = slugify(force_unicode(normalize_name(p.__class__.__name__)))
                url_patterns += patterns('',
                                         url(r'^plugin/%s/' % (slug,), include(p.plugin_urls)),
                )
        finally:
            # Reactivate translation
            activate(lang)

        return url_patterns


plugin_pool = PluginPool()

