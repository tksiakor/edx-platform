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


@login_required
@ensure_csrf_cookie
def test_problem(request):
    '''page showing summary of tests for this problem'''

    #authentication check?!!!

    #check that the problem exists
    name = request.GET['problem']
    org = 'test'
    course = '123'
    category = 'problem'
    tag = 'i4x'
    location = Location({"name": name,'org': org, 'course': course, 'category': category, 'tag': tag})

    try:
        problem = modulestore().get_item(location)
    except:
        return HttpResponse("Problem: "+name+"  Doesn't seems to exist :(")

    #get tests for this problem
    try:
        tests = ContentTest.objects.filter(problem_location=unicode(location))
        # pass these to a template to render them

    except:
        #return blank page with option for creating a test
        HttpResponse(u'No tests for this problem yet!')
        # render_to_response('component.html', {
        # 'preview': get_module_previews(problem)[0],
        # 'editor': wrap_xmodule(problem.get_html, problem, 'xmodule_edit.html')(),
        # })
    print "\n\n\n"+str(tests.count())+'\n\n\n'

    return new_test(request, location)


    answer_dict = {u'i4x-test-123-problem-b0be451a94504a6aad56ed239bf4e70d_2_1': u'5381', u'i4x-test-123-problem-b0be451a94504a6aad56ed239bf4e70d_3_1':6}
    module = get_preview_module(0, problem)
    return_dict = module.lcp.grade_answers(answer_dict)
    # return_dict ={}

    resp_ids = []
    for r in module.lcp.responders.values():
        resp_ids.append(r.id)
    return HttpResponse(str(return_dict))


def edit_test(request):
    '''edit/create more tests for a problem'''


@login_required
@ensure_csrf_cookie
def new_test(request, location):
    '''make a new test'''

    new_test = ContentTest(problem_location=location)
    capa_module = new_test.capa_module
    capa_problem = new_test.capa_problem

    # return HttpResponse(capa_module.get_html())

    problem = modulestore().get_item(location)
    html = capa_problem.get_html()
    print html
    # return HttpResponse(capa_problem.get_html())

    request.META["CSRF_COOKIE_USED"] = True
    context = {
        'csrf': csrf(request)['csrf_token'],
        'problem_html': html+str(request.COOKIES)
    }

    return render_to_response('new_test.html', context)

@csrf_protect
@login_required
@ensure_csrf_cookie
def create_test(request):
    post = request.POST
    HttpResponse(post)