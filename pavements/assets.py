import os
import sys
import platform
import resource
import glob2
from paver.easy import task, needs, consume_args, cmdopts, no_help
from subprocess import call, Popen

from pavements.config import config
from pavements.helpers import *

THEME_NAME = os.environ.get('THEME_NAME', False)
USE_CUSTOM_THEME = THEME_NAME and not is_empty(THEME_NAME)
if USE_CUSTOM_THEME:
    THEME_ROOT = os.path.join(config['REPO_ROOT'], "themes", THEME_NAME)
    THEME_SASS = os.path.join(THEME_ROOT, "static", "sass")


def xmodule_cmd(watch=False, debug=False):
    xmodule_cmd_string = 'xmodule_assets common/static/xmodule'
    if watch:
        return ("watchmedo shell-command " +
                "--patterns='*.js;*.coffee;*.sass;*.scss;*.css' " +
                "--recursive " +
                "--command='%s' " +
                "common/lib/xmodule") % xmodule_cmd_string
    else:
        return xmodule_cmd_string

MINIMAL_DARWIN_NOFILE_LIMIT = 8000

def coffee_cmd(watch=False, debug=False):
    if watch and platform.system() == 'Darwin':
        available_files = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if available_files < MINIMAL_DARWIN_NOFILE_LIMIT:
            resource.setrlimit(resource.RLIMIT_NOFILE, MINIMAL_DARWIN_NOFILE_LIMIT)
    return 'node_modules/.bin/coffee --compile %s .' % ('--watch' if watch else '')


def sass_cmd(watch=False, debug=False):
    sass_load_paths = ["./common/static/sass"]
    sass_watch_paths = ["*/static"]
    if USE_CUSTOM_THEME:
        sass_load_paths.append(THEME_SASS)
        sass_watch_paths.append(THEME_SASS)

    return ("sass %s " % ('--debug-info' if debug else '--style compressed') +
            "--load-path %s " % (' '.join(sass_load_paths)) +
            "--require ./common/static/sass/bourbon/lib/bourbon.rb " +
            "%s %s") % ('--watch' if watch else '--update', ' '.join(sass_watch_paths))


'''
@task
@cmdopts([
    ('system=', 's', "Subsystem (lms, cms) that we're processesing"),
    ('env=', 'e', "Environment (dev, test, etc) that we're processesing")
])
def preprocess(opts):
    """Preprocess all templatized static asset files"""
    if not hasattr(opts, 'system'):
        system = 'lms'
    else:
        system = opts.system

    if not hasattr(opts, 'env'):
        env = 'dev'
    else:
        env = opts.env

    status = os.system(django_admin(system, env, "preprocess_assets"))
    if status > 0:
        print "asset preprocessing failed!"
        sys.exit()

'''


@task
def preprocess():
    """Preprocess all templatized static asset files"""
    system = 'lms'
    env = 'dev'

    status = os.system(django_admin(system, env, "preprocess_assets"))
    if status > 0:
        print "asset preprocessing failed!"
        sys.exit()

pairs = {"xmodule": "install_python_prereqs", "coffee": "install_node_prereqs", "sass": ["install_ruby_prereqs", "preprocess"]}

#############################
#
# Bare assets tasks
#
##############################


@task
@needs("pavements.prereqs.install_python_prereqs")
def assets_xmodule():
    """Compile all xmodule assets"""
    call(xmodule_cmd(watch=False, debug=False), shell=True)


@task
@needs("pavements.prereqs.install_coffee_prereqs")
def assets_coffee():
    call(coffee_cmd(watch=False, debug=False), shell=True)


@task
@needs("pavements.prereqs.install_ruby_prereqs")
def assets_sass():
    call(sass_cmd(watch=False, debug=False), shell=True)

################################
#
# Assets debug tasks
#
#################################


@task
@needs("pavements.prereqs.install_python_prereqs")
def assets_xmodule_debug():
    """Compile all xmodule assets"""
    call(xmodule_cmd(watch=False, debug=True), shell=True)


@task
@needs("pavements.prereqs.install_node_prereqs", "assets_coffee_clobber")
def assets_coffee_debug():
    call(coffee_cmd(watch=False, debug=True), shell=True)


@task
@needs("pavements.prereqs.install_ruby_prereqs", "preprocess")
def assets_sass_debug():
    call(sass_cmd(watch=False, debug=True), shell=True)

#################################
#
# Assets watch tasks
#
#################################


@task
@needs("assets_xmodule_debug")
def assets_xmodule_watch():
    """Compile all xmodule assets"""
    Popen(xmodule_cmd(watch=True, debug=True), shell=True)


@task
@needs("assets_coffee_debug")
def assets_coffee_watch():
    Popen(coffee_cmd(watch=True, debug=True), shell=True)


@task
@needs("assets_sass_debug")
def assets_sass_watch():
    Popen(sass_cmd(watch=True, debug=True), shell=True)


@task
@needs('assets_sass_watch', 'assets_coffee_watch', 'assets_xmodule_watch')
def assets_watch_all():
    pass


@task
def assets_coffee_clobber():
    """ Deletes all compiled coffeescript files"""
    path = '*/static/coffee/**/*.js'
    for file_path in glob2.glob(path):
        print 'deleting file {0}'.format(file_path)
        os.remove(file_path)

@task
@needs('pavements.assets.assets_all')
@consume_args
def gather_assets(args):
    system = args[0]
    env = args[1]
    status = os.system(django_admin(system, env, 'collectstatic', '--noinput'))
    if status > 0:
        print "collectstatic failed!"
        sys.exit()
