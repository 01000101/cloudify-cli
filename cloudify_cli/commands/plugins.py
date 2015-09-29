########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

"""
Handles all commands that start with 'cfy plugins'
"""
import os
import json
import tarfile

from cloudify_cli import utils
from cloudify_cli import messages
from cloudify_cli.logger import get_logger
from cloudify_cli.utils import print_table
from cloudify_cli.exceptions import CloudifyCliError


def validate(plugin_path):
    logger = get_logger()

    logger.info(
        messages.VALIDATING_PLUGIN.format(plugin_path.name))
    with tarfile.open(plugin_path) as tar:
        tar_members = tar.getmembers()
        module_json_path = os.path.join(tar_members[0].name, 'module.json')
        try:
            module_member = tar.getmember(module_json_path)
        except KeyError:
            raise CloudifyCliError(messages.VALIDATING_PLUGIN_FAILED
                                   .format(plugin_path, "'module.json' was not"
                                                        " found in archive"))
        try:
            json.loads(tar.extractfile(module_member).read())
        except ValueError:
            raise CloudifyCliError(messages.VALIDATING_PLUGIN_FAILED
                                   .format(plugin_path, "'module.json' is not"
                                                        " a valid json"))
    # todo(adaml): which plugin json values should be validated
    logger.info(messages.VALIDATING_PLUGIN_SUCCEEDED)


def delete(plugin_id):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    logger.info(messages.PLUGIN_DELETE.format(plugin_id, management_ip))
    client = utils.get_rest_client(management_ip)
    client.plugins.delete(plugin_id)
    logger.info(messages.PLUGIN_DELETE_SUCCEEDED)


def upload(plugin_path, plugin_id):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    if not plugin_path.name.endswith('.{0}'.format('tar.gz')):
        raise CloudifyCliError(
            "Can't publish archive {0} - it's of an unsupported archive type. "
            "Only tar.gz is supported".format(plugin_path.name))
    validate(plugin_path)
    logger.info(messages.UPLOADING_PLUGIN
                .format(plugin_path.name, management_ip))
    client = utils.get_rest_client(management_ip)
    plugin = client.plugins.upload(plugin_path.name, plugin_id)
    logger.info(messages.UPLOADING_PLUGIN_SUCCEEDED.format(plugin.id))


def download(plugin_id, output):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    logger.info(messages.DOWNLOADING_PLUGIN.format(plugin_id))
    client = utils.get_rest_client(management_ip)
    target_file = client.plugins.download(plugin_id, output)
    logger.info(messages.DOWNLOADING_PLUGIN_SUCCEEDED.format(target_file))


def ls():
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    client = utils.get_rest_client(management_ip)
    logger.info(messages.PLUGINS_LIST.format(management_ip))
    pt = utils.table(['id', 'archive_name', 'module_name', 'module_source',
                      'module_version', 'supported_platform', 'wheels',
                      'uploaded_at'],
                     data=client.plugins.list())
    print_table('plugins:', pt)
