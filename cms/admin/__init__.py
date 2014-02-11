# -*- coding: utf-8 -*-
import cms.admin.pageadmin
import cms.admin.useradmin
import cms.admin.permissionadmin
import cms.admin.settingsadmin
import cms.admin.static_placeholder
# Piggyback off admin.autodiscover() to discover cms plugins
from cms import plugin_pool
from cms.apphook_pool import apphook_pool
plugin_pool.plugin_pool.discover_plugins()

apphook_pool.discover_apps()