from django.http import HttpResponse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from models import ContentTest
from capa.capa_problem import LoncapaProblem

#csrf utilities because mako :_(
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.core.context_processors import csrf
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

#note really sure what these do
from xmodule_modifiers import replace_static_urls, wrap_xmodule
from mitxmako.shortcuts import render_to_response

from contentstore.views.preview import get_preview_module, get_module_previews


def dict_slice(d, s):
    '''returns dict of keays that start with "s"'''
    return {k: v for k, v in d.iteritems() if k.startswith(s)}


@login_required
@ensure_csrf_cookie
def test_problem(request):
    '''page showing summary of tests for this problem'''

    #authentication check?!!!

    #check that the problem exists
    problem_location = request.GET['problem']
    location = Location(problem_location)
    print location

    try:
        problem = modulestore().get_item(location)
    except:
        return HttpResponse("Problem: "+name+"  Doesn't seems to exist :(")

    # get all the tests
    tests = ContentTest.objects.filter(problem_location=problem_location)

    context = {
        'csrf': csrf(request)['csrf_token'],
        'tests': tests,
        'location': problem_location
    }

    return render_to_response('test_summary.html', context)


def edit_test(request):
    '''edit/create more tests for a problem'''


def new_test(request):
    '''display the form for creating new test'''

    # get location
    location = request.POST['location']

    # just instantiate, not placed in database
    new_test = ContentTest(problem_location=location)
    capa_module = new_test.capa_module
    capa_problem = new_test.capa_problem

    problem = modulestore().get_item(location)
    html = capa_problem.get_html()

    context = {
        'csrf': csrf(request)['csrf_token'],
        'problem_html': html
    }

    return render_to_response('test_new.html', context)


# @login_required
# @ensure_csrf_cookie
def save_test(request):
    '''
        save a test.  This can be a new test, or an update to an existing one.
        If it is a new test, there will be no test_id in the POST data
    '''

    post = request.POST
    test_id = post.get('test_id', '')
    response_dict = dict_slice(post,'input_')
    should_be = post['should_be']

    # if we are creating a new problem, create it
    if test_id == '':
        # create new ContentTest
        pass
    else:
        # Fetch existing content test from database
        # Update with new infos
        pass

    response_string = "Response Dict = " + str(response_dict) + "<br>"+"should be "+should_be+"<br>"+"Test id: "+test_id
    return HttpResponse(response_string)
