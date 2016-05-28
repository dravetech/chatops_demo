# -*- coding: utf-8 -*-
"""Common code for running ansible."""

import json
import logging
import os
import sys

import invoke

import jinja2

import jinja_filters

DEBUG = True

logger = logging.getLogger(name='ansible_deploy')

if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class FakeResult:
    """Class used to fake FakeResult and work on templating."""

    def __init__(self):
        """Instantiate FakeResult."""
        # file_name = 'tasks/helpers/fake_stdout_good.json'
        file_name = 'tasks/helpers/fake_stdout_ipv6.json'
        # file_name = 'tasks/helpers/fake_stdout_error.json'
        # file_name = 'tasks/helpers/fake_stdout_bgp.json'
        # file_name = 'tasks/helpers/fake_stdout_another.json'
        with open(file_name, mode='r') as stdout:
            self.stdout = stdout.read()
        self.stderr = ''


def _process_host(host, data, env, detail, module_name):
    logger.debug('{} - {}'.format(host, module_name))
    if 'error' in data.keys():
        template = env.get_template('play_error.j2')
        return template.render(host=host, data=data)
    elif 'results' in data.keys():
        logger.debug(data)
        output = ''
        for result in data['results']:
            output += _process_host(host, result, env, detail, module_name)
        return output
    else:
        try:
            if 'failed' in data.keys():
                detail = 'failed'
            template_name = '{}/{}.j2'.format(module_name, detail)
            template = env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound:
            logger.debug('TemplateNotFound: {}'.format(template_name))
            template_name = 'default_{}.j2'.format(detail)
            template = env.get_template(template_name)
        return template.render(host=host, data=data)


def _process_playbook(playbook, important_tasks, env, detail):
    result = []
    for task in playbook['tasks']:
        logger.debug(task['task']['name'])
        host_result = {'name': task['task']['name'], 'hosts': {}}

        for host, host_data in task['hosts'].items():
            if 'error' in host_data.keys() or task['task']['name'] in important_tasks:
                host_result['hosts'][host] = _process_host(host, host_data, env,
                                                           detail, task['task']['action'])

        logger.debug('{} is important {}'.format(task['task']['name'],
                                                 task['task']['name'] in important_tasks))
        if len(host_result['hosts']) > 0 or task['task']['name'] in important_tasks:
            logger.debug('result: {}'.format(host_result))
            result.append(host_result)

    logger.debug(result)
    return result


def process_result(result, important_tasks, detail, output_format):
    """Parse the result of the execution of a playbook and build the response.

    Args:
        result: Result of the execution of a playbook using the json callback.
        important_tasks: When prettifying the output, prettify only these tasks.
        detail: Detail level to pass to the template.
        output_format: 'raw', 'text' or 'json'.
    Returns:
        A json dict with the following main attributes:
            stdout: stdout of result
            error: True if result.stderr or if there was some issue processing the template.
            pretty_output: result.stderr if there was an error executing the play, the error
                           while processing the template or if everything went fine the result
                           of processing all the important_tasks with its corresponding template.
    """
    if detail not in ['summary', 'normal', 'details']:
        raise Exception("Please, specify the correctly level of details:",
                        " 'summary', 'normal' or 'details'")

    if output_format == 'raw':
        return(result.stdout)

    stdout = '' if result.stdout is '' else json.loads(result.stdout)
    logger.debug(important_tasks)

    if result.stderr:
        pretty_output = result.stderr
        error = True
    else:
        pretty_output = ''
        error = False

        path = '{}/templates'.format(os.path.dirname(os.path.abspath(__file__)))
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
        env.filters['diff_filter'] = jinja_filters.diff_filter
        env.filters['indent_text'] = jinja_filters.indent_text

        template = env.get_template('final_output.j2')
        for play in stdout['plays']:
            result = _process_playbook(play, important_tasks, env, detail)
            pretty_output += template.render(result=result)

        template = env.get_template('stats.j2')
        pretty_output += template.render(stats=stdout['stats'])

    if output_format == 'text':
        return pretty_output
    elif output_format == 'json':
        return json.dumps({
            'stdout': stdout,
            'pretty_output': pretty_output,
            'error': error,
        })
    else:
        raise Exception('Wrong output_format. Specify either "text" or "json".')


def run_tag(tag, hosts, additional_variables, list_hosts, detail, important_tasks, output_format):
    """Execute a tag."""
    l = '--list-hosts' if list_hosts else ''
    cli = 'ansible-playbook playbook_deploy.yml \\\n\
                    --diff\\\n\
                    -l {hosts} {l}\\\n\
                    -e "{v}"\\\n\
                    --tags {tag}'.format(hosts=hosts,
                                         tag=tag,
                                         v=additional_variables,
                                         l=l)
    logger.debug(cli)
    result = invoke.run(cli, hide='both', warn=True)
    print(process_result(result, important_tasks, detail, output_format))


def show_ops(tag, hosts, additional_variables, list_hosts, detail, important_tasks, output_format):
    """
    Execute tagged tasks from `site_show_ops.yml`.

    Args:
        tag: Which tag to execute.
        hosts: Pattern to match hosts
        additional_variables: Additional variable to pass to the play.
        list_hosts: Check which devices we are going to run against.
        detail: Detai level for the output, will be passed to the template. Can be summary, normal
                or details.
        important_tasks: List of tasks we want to print.
    """
    l = '--list-hosts' if list_hosts else ''
    cli = 'ansible-playbook playbook_show.yml \\\n\
                    -l {hosts} {l}\\\n\
                    -e "{vars}"\\\n\
                    --tags {tag}'.format(hosts=hosts,
                                         tag=tag,
                                         vars=additional_variables,
                                         l=l)
    logger.debug(cli)
    result = invoke.run(cli, hide='both', warn=True)
    print(process_result(result, important_tasks, detail, output_format))
