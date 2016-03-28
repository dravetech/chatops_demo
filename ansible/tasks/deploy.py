# -*- coding: utf-8 -*-
"""Common tasks for running ansibly."""
import invoke


def _run_playbook(playbook, hosts, extra_args=''):
    extra_args = "-e '{e}'".format(e=extra_args)
    cli = 'ansible-playbook {pb} -l {hosts} {extra_args}'.format(pb=playbook,
                                                                 hosts=hosts,
                                                                 extra_args=extra_args)
    print cli
    invoke.run(cli, pty=True)


@invoke.task
def get_bgp_neighbors(host):
    """Get BGP details for a neighbor."""
    _run_playbook('playbooks/get_bgp_neighbors.yml', host)


@invoke.task
def set_bgp_neighbor(host, peer, peer_as, commit_changes=False):
    """Set a BGP neighbor."""
    extra_args = 'peer={ip} peer_as={asn} commit_changes={c} action=set'.format(
                                                             ip=peer, asn=peer_as, c=commit_changes)
    _run_playbook('playbooks/set_bgp_neighbor.yml', host, extra_args)


@invoke.task
def remove_bgp_neighbor(host, peer, commit_changes=False):
    """Set a BGP neighbor."""
    extra_args = 'peer={ip} commit_changes={c} action=remove'.format(
                                                           ip=peer, c=commit_changes)
    _run_playbook('playbooks/set_bgp_neighbor.yml', host, extra_args)
