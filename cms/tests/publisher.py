# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.constants import PUBLISHER_STATE_PENDING, PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_DIRTY
from cms.utils.i18n import force_language
from django.core.cache import cache
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse
from cms.compat import get_user_model
from cms.api import create_page, add_plugin, create_title
from cms.management.commands import publisher_publish
from cms.models import CMSPlugin, Title
from cms.models.pagemodel import Page
from cms.plugin_pool import plugin_pool
from cms.test_utils.testcases import SettingsOverrideTestCase as TestCase
from cms.test_utils.util.context_managers import StdoutOverride, SettingsOverride

from djangocms_text_ckeditor.models import Text

class PublisherCommandTests(TestCase):
    """
    Tests for the publish command
    """

    def test_command_line_should_raise_without_superuser(self):
        raised = False
        try:
            com = publisher_publish.Command()
            com.handle_noargs()
        except CommandError:
            raised = True
        self.assertTrue(raised)

    def test_command_line_publishes_zero_pages_on_empty_db(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 0)
        self.assertEqual(published_from_output, 0)

    def test_command_line_ignores_draft_page(self):
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        create_page("The page!", "nav_playground.html", "en", published=False)

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 0)
        self.assertEqual(published_from_output, 0)

        self.assertEqual(Page.objects.public().count(), 0)

    def test_table_name_patching(self):
        """
        This tests the plugin models patching when publishing from the command line
        """
        User = get_user_model()
        User.objects.create_superuser('djangocms', 'cms@example.com', '123456')
        published = create_page("The page!", "nav_playground.html", "en", published=True)
        draft = Page.objects.drafts()[0]
        draft.reverse_id = 'a_test' # we have to change *something*
        draft.save()
        add_plugin(draft.placeholders.get(slot=u"body"),
                   u"TextPlugin", u"en", body="Test content")
        draft.publish('en')
        add_plugin(draft.placeholders.get(slot=u"body"),
                   u"TextPlugin", u"en", body="Test content")

        # Manually undoing table name patching
        Text._meta.db_table = 'djangocms_text_ckeditor_text'
        plugin_pool.patched = False

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work
            # Sanity check the database (we should have one draft and one public)
        not_drafts = len(Page.objects.filter(publisher_is_draft=False))
        drafts = len(Page.objects.filter(publisher_is_draft=True))
        self.assertEquals(not_drafts, 1)
        self.assertEquals(drafts, 1)

    def test_command_line_publishes_one_page(self):
        """
        Publisher always creates two Page objects for every CMS page,
        one is_draft and one is_public.

        The public version of the page can be either published or not.

        This bit of code uses sometimes manager methods and sometimes manual
        filters on purpose (this helps test the managers)
        """
        # we need to create a superuser (the db is empty)
        get_user_model().objects.create_superuser('djangocms', 'cms@example.com', '123456')

        # Now, let's create a page. That actually creates 2 Page objects
        create_page("The page!", "nav_playground.html", "en", published=True)
        draft = Page.objects.drafts()[0]
        draft.reverse_id = 'a_test' # we have to change *something*
        draft.save()

        pages_from_output = 0
        published_from_output = 0

        with StdoutOverride() as buffer:
            # Now we don't expect it to raise, but we need to redirect IO
            com = publisher_publish.Command()
            com.handle_noargs()
            lines = buffer.getvalue().split('\n') #NB: readlines() doesn't work

        for line in lines:
            if 'Total' in line:
                pages_from_output = int(line.split(':')[1])
            elif 'Published' in line:
                published_from_output = int(line.split(':')[1])

        self.assertEqual(pages_from_output, 1)
        self.assertEqual(published_from_output, 1)
        # Sanity check the database (we should have one draft and one public)
        not_drafts = len(Page.objects.filter(publisher_is_draft=False))
        drafts = len(Page.objects.filter(publisher_is_draft=True))
        self.assertEquals(not_drafts, 1)
        self.assertEquals(drafts, 1)

        # Now check that the non-draft has the attribute we set to the draft.
        non_draft = Page.objects.public()[0]
        self.assertEquals(non_draft.reverse_id, 'a_test')

    def tearDown(self):
        plugin_pool.patched = False
        plugin_pool.set_plugin_meta()


class PublishingTests(TestCase):
    def create_page(self, title=None, **kwargs):
        return create_page(title or self._testMethodName,
                           "nav_playground.html", "en", **kwargs)

    def test_publish_home(self):
        name = self._testMethodName
        page = self.create_page(name, published=False)
        self.assertFalse(page.publisher_public_id)
        self.assertEquals(Page.objects.all().count(), 1)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(reverse("admin:cms_page_publish_page", args=[page.pk, 'en']))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], "http://testserver/en/?edit_off")

    def test_publish_single(self):
        name = self._testMethodName
        page = self.create_page(name, published=False)
        self.assertFalse(page.is_published('en'))

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(public, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish("en")

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")

        self.assertTrue(page.is_published('en'))
        self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)
        self.assertIsNotNone(page.publisher_public)
        self.assertTrue(page.publisher_public_id)

        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(public, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

        page = Page.objects.get(pk=page.pk)

        self.assertEqual(page.get_publisher_state("en"), 0)

    def test_publish_admin(self):
        page = self.create_page("test_admin", published=False)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get(reverse("admin:cms_page_publish_page", args=[page.pk, 'en']))
            self.assertEqual(response.status_code, 302)
        page = Page.objects.get(pk=page.pk)

        self.assertEqual(page.get_publisher_state('en'), 0)

    def test_publish_wrong_lang(self):
        page = self.create_page("test_admin", published=False)
        superuser = self.get_superuser()
        with SettingsOverride(
                LANGUAGES=(('de', 'de'), ('en', 'en')),
                CMS_LANGUAGES={1: [{'code': 'en', 'name': 'en', 'fallbacks': ['fr', 'de'], 'public': True}]}
            ):
            with self.login_user_context(superuser):
                with force_language('de'):
                    response = self.client.get(reverse("admin:cms_page_publish_page", args=[page.pk, 'en']))
        self.assertEqual(response.status_code, 302)
        page = Page.objects.get(pk=page.pk)

    def test_publish_child_first(self):
        parent = self.create_page('parent', published=False)
        child = self.create_page('child', published=False, parent=parent)
        parent = parent.reload()
        self.assertFalse(parent.is_published('en'))
        self.assertFalse(child.is_published('en'))

        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published('en')

        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)

        child.publish("en")
        child = child.reload()
        self.assertTrue(child.is_published("en"))
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertIsNone(child.publisher_public)

        # Since we have no parent, the state is otherwise unchanged
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            self.assertObjectDoesNotExist(public, title_set__title=name)
            self.assertObjectDoesNotExist(published, title_set__title=name)
        parent.publish("en")
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published('en')
        # Cascade publish for all pending descendants
        for name in ('parent', 'child'):
            self.assertObjectExist(drafts, title_set__title=name)
            page = drafts.get(title_set__title=name)
            self.assertTrue(page.is_published("en"), name)
            self.assertEqual(page.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT, name)
            self.assertIsNotNone(page.publisher_public, name)
            self.assertTrue(page.publisher_public.is_published('en'), name)

            self.assertObjectExist(public, title_set__title=name)
            self.assertObjectExist(published, title_set__title=name)

    def test_simple_publisher(self):
        """
        Creates the stuff needed for these tests.
        Please keep this up-to-date (the docstring!)

                A
               / \
              B  C
        """
        # Create a simple tree of 3 pages
        pageA = create_page("Page A", "nav_playground.html", "en",
                            published=True)
        pageB = create_page("Page B", "nav_playground.html", "en", parent=pageA,
                            published=True)
        pageC = create_page("Page C", "nav_playground.html", "en", parent=pageA,
                            published=False)
        # Assert A and B are published, C unpublished
        self.assertTrue(pageA.publisher_public_id)
        self.assertTrue(pageB.publisher_public_id)
        self.assertTrue(not pageC.publisher_public_id)
        self.assertEqual(len(Page.objects.public().published("en")), 2)

        # Let's publish C now.
        pageC.publish("en")

        # Assert all are published
        self.assertTrue(pageA.publisher_public_id)
        self.assertTrue(pageB.publisher_public_id)
        self.assertTrue(pageC.publisher_public_id)
        self.assertEqual(len(Page.objects.public().published("en")), 3)

    def test_i18n_publishing(self):
        page = self.create_page('parent', published=True)
        self.assertEqual(Title.objects.all().count(), 2)
        create_title("de", "vater", page)
        self.assertEqual(Title.objects.all().count(), 3)
        self.assertEqual(Title.objects.filter(published=True).count(), 2)
        page.publish('de')
        self.assertEqual(Title.objects.all().count(), 4)
        self.assertEqual(Title.objects.filter(published=True).count(), 4)


    def test_publish_ordering(self):
        page = self.create_page('parent', published=True)
        pageA = self.create_page('pageA', parent=page, published=True)
        pageC = self.create_page('pageC', parent=page, published=True)
        pageB = self.create_page('pageB', parent=page, published=True)
        page = page.reload()
        pageB.move_page(pageA, 'right')
        pageB.publish("en")
        # pageC needs reload since B has swapped places with it
        pageC.reload().publish("en")
        pageA.publish('en')

        drafts = Page.objects.drafts().order_by('tree_id', 'lft')
        draft_titles = [(p.get_title('en'), p.lft, p.rght) for p in drafts]
        self.assertEquals([('parent', 1, 8),
                              ('pageA', 2, 3),
                              ('pageB', 4, 5),
                              ('pageC', 6, 7)], draft_titles)
        public = Page.objects.public().order_by('tree_id', 'lft')
        public_titles = [(p.get_title('en'), p.lft, p.rght) for p in public]
        self.assertEquals([('parent', 1, 8),
                              ('pageA', 2, 3),
                              ('pageB', 4, 5),
                              ('pageC', 6, 7)], public_titles)

        page.publish('en')

        drafts = Page.objects.drafts().order_by('tree_id', 'lft')
        draft_titles = [(p.get_title('en'), p.lft, p.rght) for p in drafts]
        self.assertEquals([('parent', 1, 8),
                              ('pageA', 2, 3),
                              ('pageB', 4, 5),
                              ('pageC', 6, 7)], draft_titles)
        public = Page.objects.public().order_by('tree_id', 'lft')
        public_titles = [(p.get_title('en'), p.lft, p.rght) for p in public]
        self.assertEquals([('parent', 1, 8),
                              ('pageA', 2, 3),
                              ('pageB', 4, 5),
                              ('pageC', 6, 7)], public_titles)

    def test_publish_ordering2(self):
        page = self.create_page('parent', published=False)
        pageA = self.create_page('pageA', published=False)
        pageC = self.create_page('pageC', published=False, parent=pageA)
        pageB = self.create_page('pageB', published=False, parent=pageA)
        page = page.reload()
        pageA.publish('en')
        pageB.publish('en')
        pageC.publish('en')
        page.publish('en')

        drafts = Page.objects.filter(publisher_is_draft=True).order_by('tree_id', 'lft')
        publics = Page.objects.filter(publisher_is_draft=False).order_by('tree_id', 'lft')

        x = 0
        for draft in drafts:
            self.assertEqual(draft.publisher_public_id, publics[x].pk)
            x += 1


    def test_unpublish_unpublish(self):
        name = self._testMethodName
        page = self.create_page(name, published=True)
        drafts = Page.objects.drafts()
        published = Page.objects.public().published("en")
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

        page.unpublish('en')
        self.assertFalse(page.is_published('en'))
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectDoesNotExist(published, title_set__title=name)

        page.publish('en')
        self.assertTrue(page.publisher_public_id)
        self.assertObjectExist(drafts, title_set__title=name)
        self.assertObjectExist(published, title_set__title=name)

    def test_delete_title_unpublish(self):
        page = self.create_page('test', published=True)
        sub_page = self.create_page('test2', published=True, parent=page)
        self.assertTrue(sub_page.publisher_public.is_published('en'))
        page.title_set.all().delete()
        self.assertFalse(sub_page.publisher_public.is_published('en', force_reload=True))

    def test_modify_child_while_pending(self):
        home = self.create_page("Home", published=True, in_navigation=True)
        child = self.create_page("Child", published=True, parent=home,
                                 in_navigation=False)
        home = home.reload()
        home.unpublish('en')
        self.assertEqual(Title.objects.count(), 4)
        child = child.reload()
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertFalse(child.in_navigation)
        self.assertFalse(child.publisher_public.in_navigation)

        child.in_navigation = True
        child.save()
        child.publish('en')
        child = self.reload(child)
        self.assertEqual(Title.objects.count(), 4)

        self.assertTrue(child.is_published('en'))
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertTrue(child.in_navigation)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        home.publish('en')
        child = self.reload(child)
        self.assertTrue(child.is_published('en'))
        self.assertTrue(child.publisher_public_id)
        self.assertTrue(child.publisher_public.in_navigation)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

    def test_republish_with_descendants(self):
        home = self.create_page("Home", published=True)
        child = self.create_page("Child", published=True, parent=home)
        gc = self.create_page("GC", published=True, parent=child)
        self.assertTrue(child.is_published("en"))
        self.assertTrue(gc.is_published('en'))
        home = home.reload()
        home.unpublish('en')
        child = self.reload(child)
        gc = self.reload(gc)
        self.assertTrue(child.is_published("en"))
        self.assertTrue(gc.is_published("en"))
        self.assertFalse(child.publisher_public.is_published("en"))
        self.assertFalse(gc.publisher_public.is_published('en'))
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertEqual(gc.get_publisher_state('en'), PUBLISHER_STATE_PENDING)

        home.publish('en')
        child = self.reload(child)
        gc = self.reload(gc)

        self.assertTrue(child.publisher_public_id)
        self.assertTrue(gc.is_published('en'))
        self.assertTrue(child.is_published('en'))
        self.assertTrue(gc.publisher_public_id)
        self.assertEqual(child.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)
        self.assertEqual(gc.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

    def test_republish_with_dirty_children(self):
        home = self.create_page("Home", published=True)
        dirty1 = self.create_page("Dirty1", published=True, parent=home)
        dirty2 = self.create_page("Dirty2", published=True, parent=home)
        home = self.reload(home)
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        dirty1.in_navigation = True
        dirty1.save()
        home.unpublish('en')
        dirty2.in_navigation = True
        dirty2.save()
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.is_published)
        self.assertTrue(dirty2.publisher_public_id)
        self.assertEqual(dirty1.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

        home = self.reload(home)
        home.publish('en')
        dirty1 = self.reload(dirty1)
        dirty2 = self.reload(dirty2)
        self.assertTrue(dirty1.is_published("en"))
        self.assertTrue(dirty2.is_published("en"))
        self.assertTrue(dirty1.publisher_public.is_published("en"))
        self.assertTrue(dirty2.publisher_public.is_published("en"))
        self.assertEqual(dirty1.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertEqual(dirty2.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)

    def test_republish_with_unpublished_child(self):
        """
        Unpub1 was never published, and unpub2 has been unpublished after the
        fact. None of the grandchildren should become published.
        """
        home = self.create_page("Home", published=True)
        unpub1 = self.create_page("Unpub1", published=False, parent=home)
        unpub2 = self.create_page("Unpub2", published=True, parent=home)
        gc1 = self.create_page("GC1", published=True, parent=unpub1)
        gc2 = self.create_page("GC2", published=True, parent=unpub2)
        self.assertFalse(gc1.publisher_public_id)
        self.assertFalse(gc1.publisher_public_id)
        self.assertTrue(gc1.is_published('en'))
        self.assertTrue(gc2.is_published('en'))
        home.unpublish('en')
        unpub1 = self.reload(unpub1)
        unpub2.unpublish('en')  # Just marks this as not published
        for page in (unpub1, unpub2):
            self.assertFalse(page.is_published('en'), page)
            self.assertEqual(page.get_publisher_state("en"), PUBLISHER_STATE_DIRTY)
        self.assertIsNone(unpub1.publisher_public)
        self.assertIsNotNone(unpub2.publisher_public)
        self.assertFalse(unpub2.publisher_public.is_published('en'))

        gc1 = self.reload(gc1)
        gc2 = self.reload(gc2)
        for page in (gc1, gc2):
            self.assertTrue(page.is_published('en'))
            self.assertEqual(page.get_publisher_state('en'), PUBLISHER_STATE_PENDING)
        self.assertIsNone(gc1.publisher_public)
        self.assertIsNotNone(gc2.publisher_public)
        self.assertFalse(gc2.publisher_public.is_published('en'))


    def test_unpublish_with_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        self.create_page("Grandchild", parent=child, published=True)
        page = page.reload()
        child.reload()
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")
        self.assertEqual(published.count(), 3)
        self.assertEqual(page.get_descendant_count(), 2)
        base = reverse('pages-root')

        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            self.assertTrue(item.publisher_public_id)
            self.assertEqual(item.get_publisher_state('en'), PUBLISHER_STATE_DEFAULT)

        self.assertTrue(page.unpublish('en'), 'Unpublish was not successful')
        self.assertFalse(page.is_published('en'))
        cache.clear()
        for url in (base, base + 'child/', base + 'child/grandchild/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

        for title in ('Page', 'Child', 'Grandchild'):
            self.assertObjectExist(drafts, title_set__title=title)
            self.assertObjectExist(public, title_set__title=title)
            self.assertObjectDoesNotExist(published, title_set__title=title)
            item = drafts.get(title_set__title=title)
            if title == 'Page':
                self.assertFalse(item.is_published("en"))
                self.assertFalse(item.publisher_public.is_published("en"))
                # Not sure what the proper state of these are after unpublish
                #self.assertEqual(page.publisher_state, PUBLISHER_STATE_DEFAULT)
                self.assertTrue(page.is_dirty('en'))
            else:
                # The changes to the published subpages are simply that the
                # published flag of the PUBLIC instance goes to false, and the
                # publisher state is set to mark waiting for parent
                self.assertTrue(item.is_published('en'), title)
                self.assertFalse(item.publisher_public.is_published('en'), title)
                self.assertEqual(item.get_publisher_state('en'), PUBLISHER_STATE_PENDING,
                                 title)
                self.assertFalse(item.is_dirty('en'), title)

    def test_unpublish_with_dirty_descendants(self):
        page = self.create_page("Page", published=True)
        child = self.create_page("Child", parent=page, published=True)
        gchild = self.create_page("Grandchild", parent=child, published=True)
        drafts = Page.objects.drafts()
        public = Page.objects.public()
        published = Page.objects.public().published("en")
        child.in_navigation = True
        child.save()

        self.assertTrue(child.is_dirty("en"))
        self.assertFalse(gchild.is_dirty('en'))
        self.assertTrue(child.publisher_public.is_published('en'))
        self.assertTrue(gchild.publisher_public.is_published('en'))

        page.unpublish('en')
        child = self.reload(child)
        gchild = self.reload(gchild)
        # Descendants keep their dirty status after unpublish
        self.assertTrue(child.is_dirty('en'))
        self.assertFalse(gchild.is_dirty('en'))
        # However, their public version is still removed no matter what
        self.assertFalse(child.publisher_public.is_published('en'))
        self.assertFalse(gchild.publisher_public.is_published('en'))

    def test_republish_multiple_root(self):
        # TODO: The paths do not match expected behaviour
        home = self.create_page("Page", published=True)
        other = self.create_page("Another Page", published=True)
        child = self.create_page("Child", published=True, parent=home)
        child2 = self.create_page("Child", published=True, parent=other)
        self.assertTrue(Page.objects.filter(is_home=True).count(), 2)
        self.assertTrue(home.is_home)

        home = home.reload()
        self.assertTrue(home.publisher_public.is_home)
        root = reverse('pages-root')
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root + 'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'child/')
        self.assertEqual(other.get_absolute_url(), root + 'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root + 'another-page/')
        self.assertEqual(child2.get_absolute_url(), root + 'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'another-page/child/')
        home = self.reload(home)
        home.unpublish('en')
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertFalse(home.is_home)
        self.assertFalse(home.publisher_public.is_home)
        self.assertTrue(other.is_home)
        self.assertTrue(other.publisher_public.is_home)

        self.assertEqual(other.get_absolute_url(), root)
        self.assertEqual(other.get_public_object().get_absolute_url(), root)
        self.assertEqual(home.get_absolute_url(), root + 'page/')
        self.assertEqual(home.get_public_object().get_absolute_url(), root + 'page/')

        self.assertEqual(child.get_absolute_url(), root + 'page/child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'page/child/')
        self.assertEqual(child2.get_absolute_url(), root + 'child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'child/')
        home.publish('en')
        home = self.reload(home)
        other = self.reload(other)
        child = self.reload(child)
        child2 = self.reload(child2)
        self.assertTrue(home.is_home)
        self.assertTrue(home.publisher_public.is_home)
        self.assertEqual(home.get_absolute_url(), root)
        self.assertEqual(home.get_public_object().get_absolute_url(), root)
        self.assertEqual(child.get_absolute_url(), root + 'child/')
        self.assertEqual(child.get_public_object().get_absolute_url(), root + 'child/')
        self.assertEqual(other.get_absolute_url(), root + 'another-page/')
        self.assertEqual(other.get_public_object().get_absolute_url(), root + 'another-page/')
        self.assertEqual(child2.get_absolute_url(), root + 'another-page/child/')
        self.assertEqual(child2.get_public_object().get_absolute_url(), root + 'another-page/child/')

    def test_revert_contents(self):
        user = self.get_superuser()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           created_by=user)
        placeholder = page.placeholders.get(slot=u"body")
        deleted_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Deleted content")
        text_plugin = add_plugin(placeholder, u"TextPlugin", u"en", body="Public content")
        page.publish('en')

        # Modify and delete plugins
        text_plugin.body = "<p>Draft content</p>"
        text_plugin.save()
        deleted_plugin.delete()
        self.assertEquals(CMSPlugin.objects.count(), 3)

        # Now let's revert and restore
        page.revert('en')
        self.assertEquals(page.get_publisher_state("en"), PUBLISHER_STATE_DEFAULT)

        self.assertEquals(CMSPlugin.objects.count(), 4)
        plugins = CMSPlugin.objects.filter(placeholder__page=page)
        self.assertEquals(plugins.count(), 2)

        plugins = [plugin.get_plugin_instance()[0] for plugin in plugins]
        self.assertEquals(plugins[0].body, "Deleted content")
        self.assertEquals(plugins[1].body, "Public content")

    def test_revert_move(self):
        parent = create_page("Parent", "nav_playground.html", "en", published=True)
        parent_url = parent.get_absolute_url()
        page = create_page("Page", "nav_playground.html", "en", published=True,
                           parent=parent)
        other = create_page("Other", "nav_playground.html", "en", published=True)
        other_url = other.get_absolute_url()

        child = create_page("Child", "nav_playground.html", "en", published=True,
                            parent=page)
        parent = parent.reload()
        page = page.reload()
        self.assertEqual(page.get_absolute_url(), parent_url + "page/")
        self.assertEqual(child.get_absolute_url(), parent_url + "page/child/")

        # Now let's move it (and the child)
        page.move_page(other)
        page = self.reload(page)
        child = self.reload(child)
        self.assertEqual(page.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.get_absolute_url(), other_url + "page/child/")
        # Public version changed the url as well
        self.assertEqual(page.publisher_public.get_absolute_url(), other_url + "page/")
        self.assertEqual(child.publisher_public.get_absolute_url(), other_url + "page/child/")

    def test_publish_works_with_descendants(self):
        """
        For help understanding what this tests for, see:
        http://articles.sitepoint.com/print/hierarchical-data-database

        Creates this published structure:
                            home
                          /      \
                       item1   item2
                              /     \
                         subitem1 subitem2
        """
        home_page = create_page("home", "nav_playground.html", "en",
                                published=True, in_navigation=False)

        create_page("item1", "nav_playground.html", "en", parent=home_page,
                    published=True)
        item2 = create_page("item2", "nav_playground.html", "en", parent=home_page,
                            published=True)

        create_page("subitem1", "nav_playground.html", "en", parent=item2,
                    published=True)
        create_page("subitem2", "nav_playground.html", "en", parent=item2,
                    published=True)
        item2 = item2.reload()
        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('lft'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('lft'))

        self.assertEquals(len(not_drafts), 5)
        self.assertEquals(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            if public.parent:
                # Let's assert the MPTT tree is consistent
                self.assertTrue(public.lft > public.parent.lft)
                self.assertTrue(public.rght < public.parent.rght)
                self.assertEquals(public.tree_id, public.parent.tree_id)
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                # Same principle for the draft tree
                self.assertTrue(draft.lft > draft.parent.lft)
                self.assertTrue(draft.rght < draft.parent.rght)
                self.assertEquals(draft.tree_id, draft.parent.tree_id)
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

        # Now call publish again. The structure should not change.
        item2.publish('en')

        not_drafts = list(Page.objects.filter(publisher_is_draft=False).order_by('lft'))
        drafts = list(Page.objects.filter(publisher_is_draft=True).order_by('lft'))

        self.assertEquals(len(not_drafts), 5)
        self.assertEquals(len(drafts), 5)

        for idx, draft in enumerate(drafts):
            public = not_drafts[idx]
            # Check that a node doesn't become a root node magically
            self.assertEqual(bool(public.parent_id), bool(draft.parent_id))
            if public.parent:
                # Let's assert the MPTT tree is consistent
                self.assertTrue(public.lft > public.parent.lft)
                self.assertTrue(public.rght < public.parent.rght)
                self.assertEquals(public.tree_id, public.parent.tree_id)
                self.assertTrue(public.parent in public.get_ancestors())
                self.assertTrue(public in public.parent.get_descendants())
                self.assertTrue(public in public.parent.get_children())
            if draft.parent:
                # Same principle for the draft tree
                self.assertTrue(draft.lft > draft.parent.lft)
                self.assertTrue(draft.rght < draft.parent.rght)
                self.assertEquals(draft.tree_id, draft.parent.tree_id)
                self.assertTrue(draft.parent in draft.get_ancestors())
                self.assertTrue(draft in draft.parent.get_descendants())
                self.assertTrue(draft in draft.parent.get_children())

