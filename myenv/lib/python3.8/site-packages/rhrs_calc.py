# https://gist.github.com/sirosen/ec4196fee9779e5de865b0d03f12f0c8
# https://unix.stackexchange.com/questions/481939/how-to-export-a-gpg-private-key-and-public-key-to-a-file
# https://unix.stackexchange.com/questions/481939/how-to-export-a-gpg-private-key-and-public-key-to-a-file
import os
import sys
import pgpy
import sysconfig
import json
import hashlib

from zipfile import ZipFile

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext


RUNTIME_PYTHON_VER = '.'.join(list(map(str, sys.version_info[0:3])))

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


def get_plugin_hash(PLUGIN_EXEC_PATH):

    with open(PLUGIN_EXEC_PATH, "rb") as f:
        bites = f.read()  # read file as bytes
        readable_hash = hashlib.md5(bites).hexdigest()

    return readable_hash


def generate_signed_certificate(
    PRIVATE_KEY_PATH,
    PLUGIN_EXEC_PATH,
    PLUGIN_PROP_PATH,
    PLUGIN_CERT_PATH
):

    PRIVATE_KEY_UNLOCK_PASSPHRASE = os.environ.get(
        'PAYROLL_PLUGIN_PRIVATE_KEY_UNLOCK_PASSPHRASE',
        'hellonepal'
    )

    KEY_SERVER = os.environ.get(
        'PGP_KEY_SERVER',
        'keyserver.ubuntu.com'  # used key id pgp key server
    )

    KEY_ID = os.environ.get(
        'PGP_KEY_ID',
        # should be the key id of used public key
        '7CD101550CA35EF150E3AC78E5AEBC25530F34AC'
    )

    PLUGIN_NAME = os.environ.get(
        'PLUGIN_NAME',
        'default plugin name'
    )

    PLUGIN_VERSION = os.environ.get(
        'PLUGIN_VERSION',
        'default.version'
    )

    PLUGIN_DESCRIPTION = os.environ.get(
        'PLUGIN_DESCRIPTION',
        'This is plugin description'
    )

    PLUGIN_REPOSITORY = os.environ.get(
        'PLUGIN_REPOSITORY',
        'git:22'
    )

    PLUGIN_DEPENDENCY_REPOSITORIES = os.environ.get(
        'PLUGIN_DEPENDENCY_REPOSITORIES',
        'hello/hello:1, hi/hi:2'  # Comma separated value
    )
    
    private_key, _ = pgpy.PGPKey.from_file(PRIVATE_KEY_PATH)

    subjects_dict = dict(
        name=PLUGIN_NAME,
        version=PLUGIN_VERSION,
        repository=PLUGIN_REPOSITORY,
        dependencies=PLUGIN_DEPENDENCY_REPOSITORIES,
        description=PLUGIN_DESCRIPTION,
        checksum=get_plugin_hash(PLUGIN_EXEC_PATH),
        buildPythonVersion=RUNTIME_PYTHON_VER,
        signedByKeyId=KEY_ID,
        pgpKeyServer=KEY_SERVER
    )

    subjects_message = json.dumps(
        subjects_dict,
        indent=4
    )

    signature = None
    with private_key.unlock(
        PRIVATE_KEY_UNLOCK_PASSPHRASE
    ) as unlocked_private_key:
        signature = str(
            unlocked_private_key.sign(subjects_message)
        )

    with open(
        PLUGIN_PROP_PATH,
        'w+'
    ) as prop_file:
        prop_file.write(
            subjects_message
        )

    with open(
        PLUGIN_CERT_PATH,
        'w+'
    ) as cert_file:
        cert_file.write(
            signature
        )


def compile_plugin(SCRIPT_PATH, DIST_PATH):

    setup(
        fullname="plugin",
        ext_modules=cythonize(
            SCRIPT_PATH,
            compiler_directives={
                'language_level': sys.version_info[0],
                'always_allow_keywords': True
            }
        ),
        script_args=['build'],
        options={
            'build': {
                'build_lib': DIST_PATH,
                'build_temp': DIST_PATH
            }
        },
        cmdclass={'build_ext': BuildExtWithoutPlatformSuffix}
    )


def build_plugin(src_root=None, env=dict()):

    os.environ.update(env)

    PLUGIN_NAME = os.environ.get(
        'PLUGIN_NAME',
        'default plugin name'
    )

    PLUGIN_VERSION = os.environ.get(
        'PLUGIN_VERSION',
        'default.version'
    )

    SRC_ROOT =src_root or os.path.dirname(
        os.path.abspath(__file__)
    )

    PLUGIN_SCRIPT_PATH = os.path.join(
        SRC_ROOT, 'plugin.py'
    )

    DIST_PATH = os.path.join(
        SRC_ROOT, 'dist'
    )

    compile_plugin(
        PLUGIN_SCRIPT_PATH,
        DIST_PATH
    )

    PLUGIN_EXEC_PATH = os.path.join(
        DIST_PATH,
        'plugin.so'
    )

    PLUGIN_PROP_PATH = os.path.join(
        DIST_PATH,
        'plugin.props.json'
    )

    PLUGIN_CERT_PATH = os.path.join(
        DIST_PATH,
        'plugin.sig'
    )

    PRIVATE_KEY_PATH = os.path.join(
        SRC_ROOT,
        'private_key.pgp'
    )

    PUBLIC_KEY_PATH = os.path.join(
        SRC_ROOT,
        'public_key.pgp'
    )

    generate_signed_certificate(
        PRIVATE_KEY_PATH,
        PLUGIN_EXEC_PATH,
        PLUGIN_PROP_PATH,
        PLUGIN_CERT_PATH
    )

    INSTALLABLE_PLUGIN_PATH = os.path.join(
        DIST_PATH,
        f'{PLUGIN_NAME}-{PLUGIN_VERSION}-py{RUNTIME_PYTHON_VER}.zip'
    )

    with ZipFile(INSTALLABLE_PLUGIN_PATH, 'w') as zipObj:
        zipObj.write(
            PLUGIN_EXEC_PATH,
            arcname='plugin.so'
        )
        zipObj.write(
            os.path.join(
                PLUGIN_CERT_PATH
            ),
            arcname='plugin.sig'
        )

        zipObj.write(
            os.path.join(
                PLUGIN_PROP_PATH
            ),
            arcname='plugin.props.json'
        )

    return INSTALLABLE_PLUGIN_PATH
