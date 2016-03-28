# -*- coding: utf-8 -*-
"""Common tasks for ansible."""

import invoke

from . import deploy

ns = invoke.Collection()
ns.add_collection(invoke.Collection.from_module(deploy))
