# -*- coding: utf-8 -*-
"""Common tasks for running ansibly."""
import invoke
import logging
import sys

import helpers.ansible_helper as ansible_helper

logger = logging.getLogger(name='ansible_deploy')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


@invoke.task(help={'hosts': 'Which host to operate on.',
                   'list-hosts': 'Checks which devices we are going to run against.',
                   'detail': 'Detail level of the output, can be summary, normal, details',
                   'output_format': "'text' or 'json'"})
def bgp_neighbors(hosts, list_hosts=False, detail='normal', output_format='text'):
    """Get BGP neighbor state and statistics from the device."""
    important_tasks = ['Get BGP neighbors']
    tag = 'show_bgp_neighbors'
    additional_variables = ''
    ansible_helper.show_ops(tag, hosts, additional_variables, list_hosts, detail,
                            important_tasks, output_format)
