from __future__ import absolute_import, unicode_literals, print_function

import hashlib
import json
import os
import shutil
import sys
import uuid
import zipfile

import pgpy
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from hkp4py import KeyServer

from irhrs.common.models import BaseModel
from irhrs.organization.models import Organization

PAYROLL_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PLUGIN_MODULE_DIR = os.path.join(PAYROLL_APP_DIR, 'plugins')

plugin_storage = FileSystemStorage(location=PLUGIN_MODULE_DIR)


def validate_plugin_name(value):
    ''' Name validation should be done in the
    way heading name is done.
    '''
    value = value.replace('-', ' ')
    value = ' '.join(value.split())
    if not value.replace(' ', '').isalpha():
        raise ValidationError(
            'Only alphabetic characters are accepted')


def get_plugin_hash(PLUGIN_EXEC_PATH):

    with open(PLUGIN_EXEC_PATH, "rb") as f:
        bites = f.read()  # read file as bytes
        readable_hash = hashlib.md5(bites).hexdigest()

    return readable_hash


class InvalidPluginError(ValidationError):
    def __init__(self, *args, **kwargs):
        path_to_delete = kwargs.pop('path_to_delete')
        shutil.rmtree(path_to_delete)
        super().__init__(*args, **kwargs)


class PayrollVariablePlugin(BaseModel):
    # TODO @wrufesh delete installed modules on delete

    organization = models.ForeignKey(
        Organization,
        related_name='payroll_variable_plugins',
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=200,
        validators=[validate_plugin_name],
        blank=True
    )

    module_props = models.JSONField()

    signature = models.TextField()

    module = models.BinaryField(
        editable=True
    )

    class Meta:
        unique_together = (('name', 'organization'),)

    def delete_temp(self, path):
        shutil.rmtree(path)

    def clean(self):

        from irhrs.payroll.utils.calculator_variable import CalculatorVariable

        temp_dir_name = str(uuid.uuid4())

        if not os.path.exists(PLUGIN_MODULE_DIR):
            os.mkdir(PLUGIN_MODULE_DIR)

        TEMP_DIR_PATH = os.path.join(
            PLUGIN_MODULE_DIR,
            temp_dir_name
        )

        os.mkdir(TEMP_DIR_PATH)

        TEMP_PLUGIN_ZIP_FILE = os.path.join(
            TEMP_DIR_PATH,
            'plugin.zip'
        )

        with open(TEMP_PLUGIN_ZIP_FILE, 'wb+') as f:
            f.write(self.module)

        # [START] Check is the uploaded plugin file is proper zip

        if not zipfile.is_zipfile(TEMP_PLUGIN_ZIP_FILE):
            raise InvalidPluginError(
                'Module zip file is corrupted',
                path_to_delete=TEMP_DIR_PATH
            )

        # [END]

        # [START] Extract zip file and check for
        # required files

        DIR_TO_EXTRACT = os.path.join(
            TEMP_DIR_PATH,
            'plugin'
        )

        os.mkdir(DIR_TO_EXTRACT)

        with zipfile.ZipFile(TEMP_PLUGIN_ZIP_FILE, 'r') as zf:
            zf.extractall(DIR_TO_EXTRACT)

        EXTRACTED_CERT_FILE = os.path.join(
            DIR_TO_EXTRACT,
            'plugin.sig'
        )

        EXTRACTED_PROP_FILE = os.path.join(
            DIR_TO_EXTRACT,
            'plugin.props.json'
        )

        EXTRACTED_MODULE_FILE = os.path.join(
            DIR_TO_EXTRACT,
            'plugin.so'
        )

        if not os.path.exists(
            EXTRACTED_MODULE_FILE
        ):
            raise InvalidPluginError(
                'No plugin.so file in module zip file',
                path_to_delete=TEMP_DIR_PATH
            )

        if not os.path.exists(
            EXTRACTED_PROP_FILE
        ):
            raise InvalidPluginError(
                'No plugin.prop.json file in module zip file',
                path_to_delete=TEMP_DIR_PATH
            )

        plugin_props = ""
        with open(EXTRACTED_PROP_FILE, 'r') as f:
            plugin_props = f.read()

        try:
            keyserver = KeyServer(
                f'hkps://{settings.GPG_KEY_SERVER}'
            )

            keys = keyserver.search('0x{}'.format(
                settings.HRIS_KEY_ID
            ), exact=True)

            trusted_pub_key = keys[0].retrieve() if keys else ''
        except:
            raise InvalidPluginError(
                'Cannot retrieve key from keyserver. Check GPG_KEY_SERVER and HRIS_KEY_ID settings.',
                path_to_delete=TEMP_DIR_PATH
            )

        signature = pgpy.PGPSignature.from_file(EXTRACTED_CERT_FILE)

        public_key, _ = pgpy.PGPKey.from_blob(trusted_pub_key.encode())

        is_valid = public_key.verify(plugin_props, signature)

        if not is_valid:
            raise InvalidPluginError(
                'Uploaded plugin cannot be trusted',
                path_to_delete=TEMP_DIR_PATH
            )

        plugin_props_dict = json.loads(plugin_props)


        if not plugin_props_dict.get('checksum') == get_plugin_hash(EXTRACTED_MODULE_FILE):
            raise InvalidPluginError(
                'Uploaded plugin cannot be trusted',
                path_to_delete=TEMP_DIR_PATH
            )

        module_registered_name = plugin_props_dict.get(
            'name'
        )

        applied_plugin_name = self.name if self.name else module_registered_name

        applied_plugin_name = applied_plugin_name.replace('-', ' ')

        generated_variable_name = CalculatorVariable.calculator_variable_name_from_heading_name(
            applied_plugin_name
        )

        if generated_variable_name in list(
            CalculatorVariable.get_all_calculator_variables(
                self.organization.slug
            )
        ):
            raise InvalidPluginError(
                'Given name clases with existing calculator variables',
                path_to_delete=TEMP_DIR_PATH
            )

        # [END]

        # START verify if the plugin can be loaded
        import importlib

        try:
            importlib.import_module(
                f'irhrs.payroll.plugins.{temp_dir_name}.plugin.plugin'
            )
        except:
            build_py_version = plugin_props_dict.get('buildPythonVersion')
            runtime_py_version = '.'.join(list(map(str, sys.version_info[0:3])))
            raise InvalidPluginError(
                f'Plugin current runtime python version doesnot support plugin compile time python version.Build: {build_py_version}, Runtime {runtime_py_version}',
                path_to_delete=TEMP_DIR_PATH
            )

        # END

        self.name = applied_plugin_name
        self.module_props = plugin_props

        self.signature = str(signature)

        module_value = None

        with open(EXTRACTED_MODULE_FILE, 'rb') as f:
            module_value = f.read()

        self.module = module_value

        shutil.rmtree(TEMP_DIR_PATH)

    def __str__(self):
        return self.name
