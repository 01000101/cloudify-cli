########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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
# * See the License for the specific language governing permissions and
#    * limitations under the License.

"""
Handles all commands that start with 'cfy executions'
"""

import time

from cloudify_rest_client import exceptions
from cloudify_cli import utils
from cloudify_cli.exceptions import CloudifyCliError
from cloudify_cli.exceptions import SuppressedCloudifyCliError
from cloudify_cli.exceptions import ExecutionTimeoutError
from cloudify_cli.logger import get_logger
from cloudify_cli.execution_events_fetcher import (
    wait_for_execution,
    wait_for_cancel)
from cloudify_cli.logger import get_events_logger


def get(execution_id):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    client = utils.get_rest_client(management_ip)

    try:
        logger.info('Getting execution: '
                    '\'{0}\' [manager={1}]'
                    .format(execution_id, management_ip))
        execution = client.executions.get(execution_id)
    except exceptions.CloudifyClientError, e:
        if e.status_code != 404:
            raise
        msg = ("Execution '{0}' not found on management server"
               .format(execution_id))
        raise CloudifyCliError(msg)

    pt = utils.table(['id', 'workflow_id', 'status', 'deployment_id',
                      'created_at', 'error'],
                     [execution])
    pt.max_width = 50
    utils.print_table('Executions:', pt)

    # print execution parameters
    logger.info('Execution Parameters:')
    for param_name, param_value in utils.decode_dict(
            execution.parameters).iteritems():
        logger.info('\t{0}: \t{1}'.format(param_name, param_value))
    logger.info('')


def ls(deployment_id):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    client = utils.get_rest_client(management_ip)
    try:
        if deployment_id:
            logger.info('Getting executions list for deployment: \'{0}\' '
                        '[manager={1}]'.format(deployment_id, management_ip))
        else:
            logger.info(
                'Getting a list of all executions: [manager={0}]'.format(
                    management_ip))
        executions = client.executions.list(deployment_id=deployment_id)
    except exceptions.CloudifyClientError, e:
        if not e.status_code != 404:
            raise
        msg = ('Deployment {0} does not exist on management server'
               .format(deployment_id))
        raise CloudifyCliError(msg)

    columns = ['id', 'workflow_id', 'deployment_id',
               'status', 'created_at']
    pt = utils.table(columns, executions)
    utils.print_table('Executions:', pt)


def start(workflow_id, deployment_id, timeout, force,
          allow_custom_parameters, include_logs, parameters):
    logger = get_logger()
    parameters = utils.inputs_to_dict(parameters, 'parameters')
    management_ip = utils.get_management_server_ip()
    logger.info("Executing workflow '{0}' on deployment '{1}' at"
                " management server {2} [timeout={3} seconds]"
                .format(workflow_id,
                        deployment_id,
                        management_ip,
                        timeout))

    events_logger = get_events_logger()

    events_message = "* Run 'cfy events list --include-logs " \
                     "--execution-id {0}' to retrieve the " \
                     "execution's events/logs"
    try:
        client = utils.get_rest_client(management_ip)
        try:
            execution = client.executions.start(
                deployment_id,
                workflow_id,
                parameters=parameters,
                allow_custom_parameters=allow_custom_parameters,
                force=force)
        except (exceptions.DeploymentEnvironmentCreationInProgressError,
                exceptions.DeploymentEnvironmentCreationPendingError) as e:
            # wait for deployment environment creation workflow
            if isinstance(
                    e,
                    exceptions.DeploymentEnvironmentCreationPendingError):
                status = 'pending'
            else:
                status = 'in progress'

            logger.info('Deployment environment creation is {0}!'.format(
                status))
            logger.info('Waiting for create_deployment_environment '
                        'workflow execution to finish...')
            now = time.time()
            wait_for_execution(client,
                               _get_deployment_environment_creation_execution(
                                   client, deployment_id),
                               events_handler=events_logger,
                               include_logs=include_logs,
                               timeout=timeout)
            remaining_timeout = time.time() - now
            timeout -= remaining_timeout
            # try to execute user specified workflow
            execution = client.executions.start(
                deployment_id,
                workflow_id,
                parameters=parameters,
                allow_custom_parameters=allow_custom_parameters,
                force=force)

        execution = wait_for_execution(client,
                                       execution,
                                       events_handler=events_logger,
                                       include_logs=include_logs,
                                       timeout=timeout)
        if execution.error:
            logger.info("Execution of workflow '{0}' for deployment "
                        "'{1}' failed. [error={2}]"
                        .format(workflow_id,
                                deployment_id,
                                execution.error))
            logger.info(events_message.format(execution.id))
            raise SuppressedCloudifyCliError()
        else:
            logger.info("Finished executing workflow '{0}' on deployment"
                        " '{1}'".format(workflow_id, deployment_id))
            logger.info(events_message.format(execution.id))
    except ExecutionTimeoutError, e:
        logger.info("Execution of workflow '{0}' "
                    "for deployment '{1}' timed out. "
                    "* Run 'cfy executions cancel "
                    "--execution-id {2}' to cancel"
                    " the running workflow."
                    .format(workflow_id, deployment_id, e.execution_id))
        events_tail_message = "* Run 'cfy events list --tail --include-logs " \
                              "--execution-id {0}' to retrieve the " \
                              "execution's events/logs"
        logger.info(events_tail_message.format(e.execution_id))
        raise SuppressedCloudifyCliError()


def cancelByDeploymentId(deployment_id, force, wait, timeout=900):
    executions = []

    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    client = utils.get_rest_client(management_ip)

# Retrieve all executions for the provided deployment
    executionsRaw = client.executions.list(
        deployment_id=deployment_id,
        _include=[
            'id',
            'status',
            'created_at'
        ]
    )

# Find only executions that aren't complete
    for execution in executionsRaw:
        logger.info('{0} is {1}' . format(
            execution['id'],
            execution['status']
        ))
        if execution['status'] == 'started':
            executions.append(execution)

    if len(executions) > 0:
        logger.info(
            '{0}Cancelling {1} execution(s) '
            'on management server {2}'
            . format(
                'Force-' if force else '',
                len(executions),
                management_ip))
    else:
        logger.info(
            'There are no active executions '
            'for the specified deployment ID')
        return

# Cancel each non-terminated execution one-by-one
    for execution in executions:
        logger.info(
            '{0}Cancelling execution {1} on '
            'management server {2}'
            . format(
                'Force-' if force else '',
                execution['id'],
                management_ip))

        client.executions.cancel(execution['id'], force)

        logger.info(
            'A cancel request for execution {0} has been '
            'sent to the management server {1}'
            . format(
                execution['id'],
                management_ip))

        logger.info(
            'To track the execution\'s status, '
            'use:\n  cfy executions get -e {0}'
            . format(
                execution['id']))

        if wait:
            try:
                logger.info('Waiting for execution {0} to '
                            'finish being cancelled'
                            .format(execution['id']))
                execution = wait_for_cancel(client,
                                            execution,
                                            timeout=timeout)

                if execution.error:
                    logger.info("Cancellation of execution '{0}' "
                                "failed. [error={2}]"
                                .format(execution['id'],
                                        execution['error']))
                    raise SuppressedCloudifyCliError()
                else:
                    logger.info("Finished cancelling execution '{0}'"
                                .format(execution['id']))
            except ExecutionTimeoutError, e:
                logger.info("Cancellation of execution '{0}' timed out. "
                            .format(e.execution_id))
                raise SuppressedCloudifyCliError()


def cancelByExecutionId(execution_id, force, wait, timeout=900):
    logger = get_logger()
    management_ip = utils.get_management_server_ip()
    client = utils.get_rest_client(management_ip)
    logger.info(
        '{0}Cancelling execution {1} on management server {2}'
        .format('Force-' if force else '', execution_id, management_ip))
    execution = client.executions.cancel(execution_id, force)
    logger.info(
        'A cancel request for execution {0} has been sent to management '
        "server {1}. To track the execution's status, use:\n"
        "cfy executions get -e {0}"
        .format(execution_id, management_ip))

    if wait:
        try:
            logger.info('Waiting for execution {0} to finish being cancelled'
                        .format(execution_id))
            execution = wait_for_cancel(client,
                                        execution,
                                        timeout=timeout)

            if execution.error:
                logger.info("Cancellation of execution '{0}' "
                            "failed. [error={2}]"
                            .format(execution_id,
                                    execution.error))
                raise SuppressedCloudifyCliError()
            else:
                logger.info("Finished cancelling execution '{0}'"
                            .format(execution_id))
        except ExecutionTimeoutError, e:
            logger.info("Cancellation of execution '{0}' timed out. "
                        .format(e.execution_id))
            raise SuppressedCloudifyCliError()


def cancel(execution_id, deployment_id, force, wait, timeout=900):
    logger = get_logger()

    if ((not execution_id) and (not deployment_id) or
            (execution_id) and (deployment_id)):
        logger.info('You must specify either an '
                    'execution ID or a deployment ID')
        raise SuppressedCloudifyCliError()

    if execution_id:
        cancelByExecutionId(execution_id, force, wait, timeout=timeout)
    elif deployment_id:
        cancelByDeploymentId(deployment_id, force, wait, timeout=timeout)


def _get_deployment_environment_creation_execution(client, deployment_id):
    executions = client.executions.list(deployment_id=deployment_id)
    for e in executions:
        if e.workflow_id == 'create_deployment_environment':
            return e
    raise RuntimeError('Failed to get create_deployment_environment '
                       'workflow execution'
                       '. Available executions: {0}'.format(executions))
