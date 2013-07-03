"""
Unit tests on the models that make up automated content testing
"""

from django.test import TestCase
from xmodule.modulestore import Location
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore
from content_testing.models import ContentTest, Response, Input


class ContentTestTest(ModuleStoreTestCase):
    '''set up a content test to test'''

    def setUp(self):
        #course in which to put the problem
        self.course = CourseFactory.create()
        assert self.course

        #make the problem
        from capa.tests.response_xml_factory import CustomResponseXMLFactory
        custom_template = "i4x://edx/templates/problem/Custom_Python-Evaluated_Input"
        self.script = """def is_prime (n):
  primality = True
  for i in range(2,int(math.sqrt(n))+1):
    if n%i == 0:
        primality = False
        break
  return primality

def test_prime(expect,ans):
  a1=int(ans[0])
  return is_prime(a1)"""

        #change the script if 1
        self.num_inputs = 2
        problem_xml = CustomResponseXMLFactory().build_xml(
            script=self.script,
            cfn='test_prime',
            num_inputs=self.num_inputs)

        self.problem = ItemFactory.create(
            parent_location=self.course.location,
            data=problem_xml,
            template=custom_template,
            num_inputs=self.num_inputs)

        #sigh
        input_id_base = self.problem.id.replace('://', '-').replace('/', '-')

        # saved responses for making tests
        self.response_dict_correct = {
            input_id_base + '_2_1': '5',
            input_id_base + '_2_2': '174440041'
        }
        self.response_dict_incorrect = {
            input_id_base + '_2_1': '4',
            input_id_base + '_2_2': '541098'
        }
        assert self.problem

        # Make a collection of ContentTests to test
        self.pass_correct = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Correct',
            response_dict=self.response_dict_correct
        )

        self.pass_incorrect = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Incorrect',
            response_dict=self.response_dict_incorrect
        )

        self.fail_correct = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Incorrect',
            response_dict=self.response_dict_correct
        )

        self.fail_incorrect = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Correct',
            response_dict=self.response_dict_incorrect
        )

class WhiteBoxTests(ContentTestTest):
    '''test that inner methods are working'''

    def test_make_capa(self):
        '''test that the capa instantiation happens properly'''
        test_model = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Correct')

        capa = test_model.capa_problem

        #assert no error
        assert self.script in capa.problem_text

    def test_create_children(self):
        '''test that the ContentTest is created with the right structure'''
        
        # import nose; nose.tools.set_trace()
        test_model = ContentTest.objects.create(
            problem_location=str(self.problem.location),
            should_be='Correct')

        #check that the response created properly
        response_set = test_model.response_set
        self.assertEqual(response_set.count(), 1)

        #and the input
        input_set = response_set.all()[0].input_set
        self.assertEqual(input_set.count(), self.num_inputs)

    def test_create_dictionary(self):
        '''tests the constructions of the response dictionary'''
        test_model = ContentTest.objects.create(
            problem_location=self.problem.location,
            should_be='Correct',
            response_dict=self.response_dict_correct
        )
        # test_model._create_children()

        created_dict = test_model._create_response_dictionary()

        self.assertEqual(self.response_dict_correct, created_dict)

    def test_update_dict(self):
        '''tests the internal functionality of updating the dictionary'''
        test_model = self.pass_correct

        #update the dictionary with wrong answers
        test_model._update_dictionary(self.response_dict_incorrect)

        #make sure the test now fails
        test_model.run()
        self.assertEqual(test_model.verdict, False)


class BlackBoxTests(ContentTestTest):
    '''test overall behavior of the ContentTest model'''

    def test_pass_correct(self):
        '''test that it passes with correct answers when it should'''

        # run the test
        self.pass_correct.run()

        # make sure it passed
        self.assertEqual(True, self.pass_correct.verdict)

    def test_fail_incorrect(self):
        '''test that it fails with incorrect answers'''

        # run the testcase
        self.fail_incorrect.run()

        # make sure it failed
        self.assertEqual(False, self.fail_incorrect.verdict)

    def test_pass_incorrect(self):
        '''test that it passes with incorrect'''

        # run the test
        self.pass_incorrect.run()

        # make sure it passed
        self.assertEqual(True, self.pass_incorrect.verdict)

    def test_fail_correct(self):
        '''test that it fails with incorrect answers'''

        # run the testcase
        self.fail_incorrect.run()

        # make sure it failed
        self.assertEqual(False, self.fail_incorrect.verdict)


    def test_reset_verdict(self):
        '''test that changing things resets the verdict'''

        test_model = self.pass_correct

        # run the testcase (generates verdict)
        test_model.run()

        # update test
        test_model.response_dict = self.response_dict_incorrect
        test_model.save()

        #ensure that verdict is now null
        self.assertEqual(None, test_model.verdict)

    def test_change_dict(self):
        '''test that the verdict changes with the new dictionary on new run'''

        test_model = self.pass_correct

        # update test
        test_model.response_dict = self.response_dict_incorrect
        test_model.save()

        # run the test
        test_model.run()

        # assert that the verdict is now False
        self.assertEqual(False, test_model.verdict)
