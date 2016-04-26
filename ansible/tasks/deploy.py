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


def _manipulate_bgp_neighbors(hosts, peer, peer_as, additional_variables, tag,
                              detail, output_format):
    important_tasks = ['Set/Remove BGP neighbors',
                       'Operation',
                       ]
    list_hosts = False
    ansible_helper.run_tag(tag, hosts, additional_variables, list_hosts, detail,
                           important_tasks, output_format)


@invoke.task
def set_bgp_neighbor(hosts, peer, peer_as, commit_changes=False,
                     detail='normal', output_format='text'):
    """Set a BGP neighbor."""
    tag = 'add_bgp_peer'
    additional_variables = 'peer={ip} peer_as={asn} commit_changes={c}'.format(
                                                   ip=peer, asn=peer_as, c=commit_changes)
    _manipulate_bgp_neighbors(hosts, peer, peer_as, additional_variables, tag,
                              detail, output_format)


@invoke.task
def remove_bgp_neighbor(hosts, peer, commit_changes=False,
                        detail='normal', output_format='text'):
    """Set a BGP neighbor."""
    tag = 'remove_bgp_peer'
    additional_variables = 'peer={ip} commit_changes={c}'.format(
                                                                ip=peer, c=commit_changes)
    _manipulate_bgp_neighbors(hosts, peer, None, additional_variables, tag, detail, output_format)
