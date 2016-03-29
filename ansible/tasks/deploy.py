# -*- coding: utf-8 -*-
"""Common tasks for running ansibly."""
import json
import invoke
import logging
import os
import sys


from jinja2 import Environment, FileSystemLoader


logger = logging.getLogger(name='ansible_deploy')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def _prettify_result(template, result, **kwargs):
    logger.debug(result)
    logger.debug(kwargs)
    path = '{}/templates'.format(os.path.dirname(os.path.abspath(__file__)))
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template(template)
    return template.render(result=result, **kwargs)


def _run_playbook(playbook, hosts, extra_args=''):
    extra_args = "-e '{e}'".format(e=extra_args)
    cli = 'ansible-playbook {pb} -l {hosts} {extra_args}'.format(pb=playbook,
                                                                 hosts=hosts,
                                                                 extra_args=extra_args)
    logger.debug(cli)
    result = invoke.run(cli, hide='both', warn=True)
    logger.debug('stdout: {}'.format(result.stdout.strip()))
    logger.debug('stderr: {}'.format(result.stderr.strip()))
    logger.debug('return_code: {}'.format(result.return_code))
    return result


def _process_result(result, template, important_tasks=None, **kwargs):
    stdout = '' if result.stdout is '' else json.loads(result.stdout)
    stderr = result.stderr

    if result.return_code in [0, 2]:
        important_tasks = [] if important_tasks is None else important_tasks
        stdout_dict = json.loads(result.stdout)
        result_dict = {}
        for t in stdout_dict['plays'][0]['tasks']:
            if t['task']['name'] in important_tasks:
                result_dict[t['task']['name']] = {host: data for host, data in t['hosts'].items()}
        logger.debug(result_dict)
        pretty = _prettify_result(template, result_dict, **kwargs)
    else:
        pretty = stderr

    return json.dumps({
        'stdout': stdout,
        'stderr': stderr,
        'pretty': pretty,
    })


@invoke.task
def get_bgp_neighbors(hosts):
    """Get BGP details for a neighbor."""
    important_tasks = ['Get BGP neighbors']
    result = _run_playbook('playbooks/get_bgp_neighbors.yml', hosts)
    print(_process_result(result, 'get_bgp_neighbors.j2', important_tasks))


def _manipulate_bgp_neighbors(hosts, peer, peer_as, commit_changes, extra_args, action):
    important_tasks = ['Set/Remove BGP neighbors']
    run_result = _run_playbook('playbooks/set_bgp_neighbor.yml', hosts, extra_args)
    print(_process_result(run_result, 'set_bgp_neighbors.j2', important_tasks, peer=peer,
                          peer_as=peer_as, action=action, commit_changes=commit_changes))


@invoke.task
def set_bgp_neighbor(hosts, peer, peer_as, commit_changes=False):
    """Set a BGP neighbor."""
    action = 'set'
    extra_args = 'peer={ip} peer_as={asn} commit_changes={c} action={a}'.format(
                                                   ip=peer, asn=peer_as, c=commit_changes, a=action)
    _manipulate_bgp_neighbors(hosts, peer, peer_as, commit_changes, extra_args, action)


@invoke.task
def remove_bgp_neighbor(hosts, peer, commit_changes=False):
    """Set a BGP neighbor."""
    action = 'remove'
    extra_args = 'peer={ip} commit_changes={c} action={a}'.format(
                                                                ip=peer, c=commit_changes, a=action)
    _manipulate_bgp_neighbors(hosts, peer, None, commit_changes, extra_args, action)
