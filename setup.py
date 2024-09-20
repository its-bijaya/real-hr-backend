"""
Usage: 'python setup.py build_ext --inplace'

Compile .py files into .so files.
    (app) -----(setup)------> (app-compile)

"""
import datetime
import multiprocessing
from subprocess import Popen

from Cython.Distutils import build_ext
import sys
import os
import re
import shutil
import fnmatch
from datetime import date
from itertools import chain
from distutils.core import setup, Extension

import sysconfig
from Cython.Build import cythonize

from config import VERSION

# Format :: (2, 5, 4, 0, 'released')
VERSION_NAME = '.'.join(map(str, VERSION[:-1]))

# the type of a compiled regex file for comparison later
retype = type(re.compile('kkk'))
_compile = re.compile


class M(object):
    """
    use this as collection to store compilable modules
    """

    def __init__(self, name, *ignored):
        self.name = name
        self.ignored = ignored


PKG_PATH = ''
THIS_FILE = os.path.abspath(__file__)
PARENT_DIRECTORY = os.path.dirname(THIS_FILE)
BUILD_DIR = 'app-compile/'
BUILD_DIR_ABS = os.path.join(PARENT_DIRECTORY, BUILD_DIR)
SOURCE_PATH_ABS = os.path.abspath('.')

# optional apps are excluded if they are not present in COMPILE_MODULES
OPTIONAL_MODULES = [
]

COMPILE_MODULES = [
    M('irhrs'),
    M('config')
]
COMPILE_MODULES_NAMES = [m.name for m in COMPILE_MODULES]

# we want the modules to be importable by django, so we do not
# compile init files
DO_NOT_COMPILE_FILES = [
    'irhrs/core/mixins/file_import_mixin.py',
    'irhrs/export/mixins/export.py',
    'irhrs/users/api/v1/serializers/user_import.py',
    'config/settings/env.py',
    'irhrs/builder/api/v1/generalized_reports/views/attendance_and_leave_report.py'
]

IGNORE_FILES = [
    '__init__.py',
    'do_not_compile.py',
    'migrations',
    *DO_NOT_COMPILE_FILES
]
# pattern should either be regex or glob as in unix shell
EXCLUDE_FILES = [
    'README.md',
    'tests',
    '*.pyc',
    '.git',
    '.gitignore',
    '*.so',
    '*.c',
    'fabfile_bck.py',
    '*.log',
    '*.ipynb',
    'scratch',
    'server_config',
    'patch',
]


def dont_copy_patterns(directory, names):
    '''
    function that returns ignored files for provided directory that match ignored
    patterns
    '''
    _fnmatch = fnmatch.fnmatch
    excluded = []

    for name in names:
        if name in OPTIONAL_MODULES and name not in COMPILE_MODULES_NAMES:
            name = '/'.join(name.split('.'))
            excluded.append(name)
        else:
            fullpath = os.path.join(directory, name)
            for pat in EXCLUDE_FILES:
                if isinstance(pat, retype):
                    exclude = pat.match(fullpath)
                else:
                    exclude = _fnmatch(name, pat)

                if exclude:
                    excluded.append(name)
    return excluded


def copy_source(dest=None):
    dest = dest or BUILD_DIR
    for folder in [
        'config',
        'fixtures',
        'irhrs',
        'requirements',
        'scripts'
    ]:
        shutil.copytree(
            folder,
            os.path.join(
                dest,
                folder
            ),
            ignore=dont_copy_patterns)
    for filename in ['manage.py', 'db_backup.py']:
        shutil.copyfile(
            filename,
            os.path.join(
                BUILD_DIR_ABS, filename
            )
        )


def is_ignored(filename, *ignores):
    '''
    return True if the filename matches the ignore patterns, this won't support
    glob patterns yet, and won't do so until we need them
    '''
    ignored = False

    for ig in chain(IGNORE_FILES, ignores):
        if filename.endswith(ig):
            ignored = True
            break
    return ignored


def _cythonize():
    '''
    this function does a few things in general,
    first of all, create a similar source tree of our project under BUILD_DIR
        where most of the py files will have been replaced by their .c and .so
        counterparts
    secondly, remove .c files
    '''
    c_files = []
    for dir_ in COMPILE_MODULES:
        for dirname, dirnames, filenames in os.walk(
                os.path.join(BUILD_DIR, dir_.name)):
            _dirname = os.path.split(dirname)[-1]
            ignored = is_ignored(_dirname, *dir_.ignored)

            if ignored:
                continue

            for filename in filenames:
                file_ = os.path.join(dirname, filename)
                stripped_name = os.path.relpath(file_, PKG_PATH)
                file_name, extension = os.path.splitext(stripped_name)

                file_ignored = is_ignored(stripped_name, *dir_.ignored)

                to_compile = extension == '.py' and not file_ignored

                if to_compile:
                    target_file = file_name + '.c'
                    c_files.append(stripped_name.replace('.py', '.c'))
                else:
                    target_file = stripped_name

                file_dir = os.path.dirname(target_file)
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)

                if to_compile:
                    cythonize(
                        stripped_name,
                        force=True,
                        compiler_directives={
                            'language_level': sys.version_info[0],
                            'always_allow_keywords': True
                        }
                    )
                    # remove the .py file after we've transpiled it to .c
                    os.remove(stripped_name)
    return c_files


def move_build_and_make_archive():
    os.chdir(SOURCE_PATH_ABS)
    todays_build = os.path.abspath('../irhrs_builds/{}'.format(date.today()))
    build_path = os.path.join(todays_build, 'app-compile')
    build_tar = '{}.tar.gz'.format(build_path)

    source_code = os.path.join(todays_build, 'backend')
    source_code_tar = '{}.tar.gz'.format(source_code)

    remove_if_exists = [build_path, build_tar, source_code, source_code_tar]

    for p in remove_if_exists:
        if os.path.exists(p):
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
    build_prod = os.path.abspath('app-compile')
    if os.path.exists(build_prod):
        print(('Moving build to {}'.format(build_path)))
        # shutil.move(build_prod, build_path)
        print('Packaging build as 7z file...')
        Popen(
            [
                '7z',
                'a',
                'app_compile_{}.7z'.format(
                    datetime.datetime.now().strftime('%d%m%Y')
                ),
                'app-compile',
            ]
        )
        return todays_build
    else:
        print('No build exists...Aborting')


def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, '')
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


class BuildExtWithoutPlatformSuffix(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        return get_ext_filename_without_platform_suffix(filename)


if __name__ == '__main__':
    if os.path.exists(BUILD_DIR):
        # if BUILD_DIR is present, just remove it because shutil.copytree
        # doesn't like it when destination directory exists
        shutil.rmtree(BUILD_DIR)

    if os.path.exists('build'):
        # although we remove this at the end, some build may have
        # stopped ungracefully and we want to start fresh
        shutil.rmtree('build')

    print('Copying source to build directory...')
    copy_source()
    # sys.exit(0)
    # write_license()
    # write_uuid_generator()

    def cythonize_and_build():
        c_files = _cythonize()
        abs_path_c_files = [os.path.abspath(c) for c in c_files]

        modules = []

        for c_file in abs_path_c_files:
            relfile = os.path.relpath(c_file, BUILD_DIR)
            filename = os.path.splitext(relfile)[0]
            # python module name style e.g. module.submodule
            ext_name = filename.replace(os.path.sep, ".")
            extension = Extension(ext_name, sources=[c_file])
            modules.append(extension)

        # we need to chdir to the build directory to work with relative paths
        os.chdir(BUILD_DIR_ABS)

        setup(name='iRealHRSoft',
              version=VERSION_NAME,
              ext_modules=cythonize(
                  modules,
                  compiler_directives={
                      'language_level': sys.version_info[0],
                      'always_allow_keywords': True
                  }
              ),
              cmdclass={'build_ext': BuildExtWithoutPlatformSuffix})

        # do some cleanup after the fact
        # we already have c files
        print('Build successful, removing .c sources...')
        for c_file in abs_path_c_files:
            os.remove(c_file)

        # clean build directory
        if os.path.exists('build'):
            print('Removing build directory...')
            shutil.rmtree('build')


    cythonize_and_build()
    tar_file = move_build_and_make_archive()

    if tar_file is None:
        print('Build was unsuccessful..Manual intervention needed..')
    else:
        print('Build successful..')
        print(('Build location: {}'.format(tar_file)))
