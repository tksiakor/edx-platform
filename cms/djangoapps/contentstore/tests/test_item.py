from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from django.core.urlresolvers import reverse
from xmodule.capa_module import CapaDescriptor
import json
from xmodule.modulestore.django import modulestore


class DeleteItem(CourseTestCase):
    def setUp(self):
        """ Creates the test course with a static page in it. """
        super(DeleteItem, self).setUp()
        self.course = CourseFactory.create(org='mitX', number='333', display_name='Dummy Course')

    def testDeleteStaticPage(self):
        # Add static tab
        data = {
            'parent_location': 'i4x://mitX/333/course/Dummy_Course',
            'category': 'static_tab'
        }

        resp = self.client.post(reverse('create_item'), data)
        self.assertEqual(resp.status_code, 200)

        # Now delete it. There was a bug that the delete was failing (static tabs do not exist in draft modulestore).
        resp = self.client.post(reverse('delete_item'), resp.content, "application/json")
        self.assertEqual(resp.status_code, 200)


class TestCreateItem(CourseTestCase):
    """
    Test the create_item handler thoroughly
    """
    def response_id(self, response):
        """
        Get the id from the response payload
        :param response:
        """
        parsed = json.loads(response.content)
        return parsed['id']

    def test_create_nicely(self):
        """
        Try the straightforward use cases
        """
        # create a chapter
        display_name = 'Nicely created'
        resp = self.client.post(
            reverse('create_item'),
            {'parent_location': self.course_location.url(),
             'display_name': display_name,
             'category': 'chapter'
            }
        )
        self.assertEqual(resp.status_code, 200)

        # get the new item and check its category and display_name
        chap_location = self.response_id(resp)
        new_obj = modulestore().get_item(chap_location)
        self.assertEqual(new_obj.category, 'chapter')
        self.assertEqual(new_obj.display_name, display_name)
        self.assertEqual(new_obj.location.org, self.course_location.org)
        self.assertEqual(new_obj.location.course, self.course_location.course)

        # get the course and ensure it now points to this one
        course = modulestore().get_item(self.course_location)
        self.assertIn(chap_location, course.children)

        # use default display name
        resp = self.client.post(
            reverse('create_item'),
            {'parent_location': chap_location,
             'category': 'vertical'
            }
        )
        self.assertEqual(resp.status_code, 200)

        vert_location = self.response_id(resp)

        # create problem w/ boilerplate
        template_id = 'multiplechoice.yaml'
        resp = self.client.post(
            reverse('create_item'),
            {'parent_location': vert_location,
             'category': 'problem',
             'boilerplate': template_id
            }
        )
        self.assertEqual(resp.status_code, 200)
        prob_location = self.response_id(resp)
        problem = modulestore('draft').get_item(prob_location)
        # ensure it's draft
        self.assertTrue(problem.is_draft)
        # check against the template
        template = CapaDescriptor.get_template(template_id)
        self.assertEqual(problem.data, template['data'])
        self.assertEqual(problem.display_name, template['metadata']['display_name'])
        self.assertEqual(problem.markdown, template['metadata']['markdown'])

    def test_create_item_negative(self):
        """
        Negative tests for create_item
        """
        # non-existent boilerplate: creates a default
        resp = self.client.post(
            reverse('create_item'),
            {'parent_location': self.course_location.url(),
             'category': 'problem',
             'boilerplate': 'nosuchboilerplate.yaml'
            }
        )
        self.assertEqual(resp.status_code, 200)
