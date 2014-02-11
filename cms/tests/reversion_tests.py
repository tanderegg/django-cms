# -*- coding: utf-8 -*-
from __future__ import with_statement
import shutil

from cms.compat import get_user_model
from cms.admin import pageadmin
from django.contrib import admin

from cms.models import Page, Title
from cms.models.pluginmodel import CMSPlugin
from djangocms_text_ckeditor.models import Text
from cms.test_utils.project.fileapp.models import FileModel
from cms.test_utils.testcases import CMSTestCase, TransactionCMSTestCase, URL_CMS_PAGE, URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADD, \
    URL_CMS_PLUGIN_ADD, URL_CMS_PLUGIN_EDIT
from cms.test_utils.util.context_managers import SettingsOverride
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from os.path import join
import reversion
from reversion.models import Revision, Version

if hasattr(reversion.models, 'VERSION_CHANGE'):
    from reversion.models import VERSION_CHANGE


class BasicReversionTestCase(CMSTestCase):
    def setUp(self):        
        self.user = self._create_user("test", True, True)

    def test_number_revisions(self):
        with self.login_user_context(self.user):
            self.assertEquals(Revision.objects.all().count(), 0)
            self.page_data = self.get_new_page_data()

            response = self.client.post(URL_CMS_PAGE_ADD, self.page_data)

            self.assertRedirects(response, URL_CMS_PAGE)
            self.assertEquals(Page.objects.all().count(), 2)
            self.assertEquals(Revision.objects.all().count(), 1)


class ReversionTestCase(TransactionCMSTestCase):
    def setUp(self):
        u = self._create_user("test", True, True)

        with self.login_user_context(u):
            # add a new text plugin
            self.page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, self.page_data)
            self.assertRedirects(response, URL_CMS_PAGE)

            page = Page.objects.all()[0]
            placeholderpk = page.placeholders.get(slot="body").pk
            plugin_data = {
                'plugin_type': "TextPlugin",
                'plugin_language': settings.LANGUAGES[0][0],
                'placeholder_id': placeholderpk,
                'plugin_parent': '',
            }
            response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
            self.assertEquals(response.status_code, 200)
            # now edit the plugin
            edit_url = URL_CMS_PLUGIN_EDIT + response.content.decode('utf8').split("edit-plugin/")[1].split("/")[
                0] + "/"
            response = self.client.get(edit_url)
            self.assertEquals(response.status_code, 200)
            response = self.client.post(edit_url, {"body": "Hello World"})
            self.assertEquals(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEquals("Hello World", txt.body)
            self.txt = txt
            # change the content
            response = self.client.post(edit_url, {"body": "Bye Bye World"})
            self.assertEquals(response.status_code, 200)
            txt = Text.objects.all()[0]
            self.assertEquals("Bye Bye World", txt.body)
            p_data = self.page_data.copy()
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.pk, p_data)
            self.assertRedirects(response, URL_CMS_PAGE)
            page.publish('en')

        self.user = u

    def test_revert(self):
        """
        Test that you can revert a plugin
        """
        with self.login_user_context(self.user):
            self.assertEquals(Page.objects.all().count(), 2)
            self.assertEquals(Title.objects.all().count(), 2)
            self.assertEquals(CMSPlugin.objects.all().count(), 2)
            self.assertEquals(Revision.objects.all().count(), 5)

            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[2]
            version = Version.objects.get(content_type=ctype, revision=revision)
            page = Page.objects.all()[0]

            history_url = URL_CMS_PAGE_CHANGE % (page.pk) + "history/"
            response = self.client.get(history_url)
            self.assertEquals(response.status_code, 200)

            revert_url = history_url + "%s/" % version.pk
            response = self.client.get(revert_url)
            self.assertEquals(response.status_code, 200)
            data = self.page_data
            response = self.client.post("%s?language=en&" % revert_url, self.page_data)
            self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page.pk)
            # test for publisher_is_draft, published is set for both draft and
            # published page
            self.assertEquals(Page.objects.all()[0].publisher_is_draft, True)
            self.assertEquals(CMSPlugin.objects.all().count(), 2)

            # test that CMSPlugin subclasses are reverted
            self.assertEquals(Text.objects.all().count(), 2)
            self.assertEquals(Text.objects.get(pk=self.txt.pk).body, "Hello World")
            self.assertEquals(Revision.objects.all().count(), 6)

    def test_undo_redo(self):
        """
        Test that you can revert a plugin
        """
        with self.login_user_context(self.user):
            self.assertEquals(Page.objects.all().count(), 2)
            self.assertEquals(Title.objects.all().count(), 2)
            self.assertEquals(CMSPlugin.objects.all().count(), 2)
            self.assertEquals(Revision.objects.all().count(), 5)

            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[2]
            version = Version.objects.get(content_type=ctype, revision=revision)
            page = Page.objects.all()[0]

            undo_url = reverse("admin:cms_page_undo", args=[page.pk])
            response = self.client.post(undo_url)
            self.assertEquals(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertTrue(page.revision_id != 0)
            rev = page.revision_id
            redo_url = reverse("admin:cms_page_redo", args=[page.pk])
            response = self.client.post(redo_url)
            self.assertEquals(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertTrue(page.revision_id != rev)
            txt = Text.objects.all()[0]
            edit_url = URL_CMS_PLUGIN_EDIT + str(txt.pk) + "/"
            response = self.client.post(edit_url, {"body": "Hello World2"})
            self.assertEquals(response.status_code, 200)
            page = Page.objects.all()[0]
            self.assertEqual(page.revision_id, 0)
            self.assertEqual(2, CMSPlugin.objects.all().count())
            placeholderpk = page.placeholders.filter(slot="body")[0].pk
            plugin_data = {
                'plugin_type': "TextPlugin",
                'plugin_language': settings.LANGUAGES[0][0],
                'placeholder_id': placeholderpk,
                'plugin_parent': '',
            }
            response = self.client.post(URL_CMS_PLUGIN_ADD, plugin_data)
            self.assertEquals(response.status_code, 200)
            # now edit the plugin
            edit_url = URL_CMS_PLUGIN_EDIT + response.content.decode('utf8').split("edit-plugin/")[1].split("/")[
                0] + "/"
            response = self.client.get(edit_url)
            self.assertEquals(response.status_code, 200)
            response = self.client.post(edit_url, {"body": "Hello World"})
            self.assertEquals(response.status_code, 200)
            self.assertEqual(3, CMSPlugin.objects.all().count())
            response = self.client.post(undo_url)
            response = self.client.post(undo_url)
            self.assertEqual(2, CMSPlugin.objects.all().count())

    def test_recover(self):
        """
        Test that you can recover a page
        """
        with self.login_user_context(self.user):
            self.assertEquals(Revision.objects.all().count(), 5)
            ctype = ContentType.objects.get_for_model(Page)
            revision = Revision.objects.all()[4]
            version = Version.objects.filter(content_type=ctype, revision=revision)[0]

            self.assertEquals(Page.objects.all().count(), 2)
            self.assertEquals(CMSPlugin.objects.all().count(), 2)
            self.assertEquals(Text.objects.all().count(), 2)

            page = Page.objects.all()[0]
            page_pk = page.pk
            page.delete()

            self.assertEquals(Page.objects.all().count(), 0)
            self.assertEquals(CMSPlugin.objects.all().count(), 0)
            self.assertEquals(Text.objects.all().count(), 0)

            recover_url = URL_CMS_PAGE + "recover/"
            response = self.client.get(recover_url)
            self.assertEquals(response.status_code, 200)

            recover_url += "%s/" % version.pk
            response = self.client.get(recover_url)
            self.assertEquals(response.status_code, 200)
            response = self.client.post(recover_url, self.page_data)
            self.assertRedirects(response, URL_CMS_PAGE_CHANGE % page_pk)
            self.assertEquals(Page.objects.all().count(), 1)
            self.assertEquals(CMSPlugin.objects.all().count(), 1)

            # test that CMSPlugin subclasses are recovered
            self.assertEquals(Text.objects.all().count(), 1)

    def test_publish(self):
        with self.login_user_context(self.user):
            page = Page.objects.all()[0]
            page_pk = page.pk
            self.assertEquals(Revision.objects.all().count(), 5)
            publish_url = URL_CMS_PAGE + "%s/en/publish/" % page_pk
            response = self.client.get(publish_url)
            self.assertEquals(response.status_code, 302)
            self.assertEquals(Revision.objects.all().count(), 2)

    def test_publish_limit(self):
        with self.login_user_context(self.user):
            with SettingsOverride(CMS_MAX_PAGE_PUBLISH_REVERSIONS=5):
                page = Page.objects.all()[0]
                page_pk = page.pk
                self.assertEquals(Revision.objects.all().count(), 5)
                for x in range(10):
                    publish_url = URL_CMS_PAGE + "%s/en/publish/" % page_pk
                    response = self.client.get(publish_url)
                    self.assertEquals(response.status_code, 302)
                self.assertEqual(Revision.objects.all().count(), 6)


class ReversionFileFieldTests(CMSTestCase):
    def tearDown(self):
        shutil.rmtree(join(settings.MEDIA_ROOT, 'fileapp'))

    def test_file_persistence(self):
        content = b'content1'
        with reversion.create_revision():
            # add a file instance
            file1 = FileModel()
            file1.test_file.save('file1.txt', SimpleUploadedFile('file1.txt', content), False)
            file1.save()
            # manually add a revision because we use the explicit way
            # django-cms uses too.
            adapter = reversion.get_adapter(FileModel)
            if hasattr(reversion.models, 'VERSION_CHANGE'):
                reversion.revision_context_manager.add_to_context(
                    reversion.default_revision_manager, file1,
                    adapter.get_version_data(file1, VERSION_CHANGE))
            else:
                reversion.revision_context_manager.add_to_context(
                    reversion.default_revision_manager, file1,
                    adapter.get_version_data(file1))
                # reload the instance from db
        file2 = FileModel.objects.all()[0]
        # delete the instance.
        file2.delete()

        # revert the old version
        file_version = reversion.get_for_object(file1)[0]
        file_version.revert()

        # reload the reverted instance and check for its content
        file1 = FileModel.objects.all()[0]
        self.assertEqual(file1.test_file.file.read(), content)
