# -*- coding: utf-8 -*-
'''
Lint states and sls files
'''
from __future__ import absolute_import

# Import python libs
import logging
from types import NoneType
from collections import OrderedDict
from voluptuous import *

# Import salt libs
import salt.config
import salt.utils
import salt.state
import salt.payload
from salt.exceptions import SaltInvocationError

__outputter__ = {
    'validate_sls': 'highstate',
}

log = logging.getLogger(__name__)

def _getschema():

    schema = {}

    # Setup dunder dicts
    __opts__ = salt.config.minion_config(os.environ.get('SALT_MINION_CONFIG', '/etc/salt/minion'))
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __opts__['pillar'] = __pillar__
    __salt__ = salt.loader.minion_mods(__opts__)

    # Get list of state modules and their arguments
    statemods = salt.loader.states(__opts__, __salt__)
    argspecs = salt.utils.argspec_report(statemods)

    # Default schema for common functions
    # Add list of valid templates
    default_schema = {
        'context': OrderedDict,
        'defaults': OrderedDict,
        'name': Coerce(str),
        'names': list,
        'check_cmd': str,
        'listen': list,
        'listen_in': list,
        'onchanges': list,
        'onchanges_in': list,
        'onfail': list,
        'onfail_in': list,
        'onlyif': Coerce(str),
        'order': int,
        'prereq': list,
        'prereq_in': list,
        'require': list,
        'require_in': list,
        'template': str,
        'unless': Coerce(str),
        'use': list,
        'watch': list,
        'watch_in': list,
        'formatter': str
    }

    # pkgrepo doesn't appear in list of state modules. Add it here.
    pkgrepo_schema = {
        'baseurl': str,
        'comments': list,
        'comps': str,
        'consolidate': bool,
        'disabled': bool,
        'dist': str,
        'file': str,
        'gpgcheck': int,
        'gpgkey': str,
        'humanname': str,
        'keyserver': str,
        'key_url': str,
        'mirrorlist': str,
        'name': str,
        'order': int,
        'ppa': str,
        'ppa_auth': str,
        'refresh_db': bool
    }
    for state in ['pkgrepo.managed', 'pkgrepo.absent']:
        schema[state] = Schema(dict(default_schema.items() + pkgrepo_schema.items()))

    # Identify arguments and default value. Add to schema dict inheriting
    # type from default value. If no default value, assume string.
    for state,specs in argspecs.iteritems():
        s = default_schema.copy()
        for idx, arg in enumerate(specs['args']):
            if arg not in s:
                if specs['defaults'] == None:
                    default = 'string'
                else:
                    nodefaults = (len(specs['args']) - len(specs['defaults']))
                    if idx < nodefaults:
                        default = 'string'
                    else:
                        didx = (idx - nodefaults)
                        default = specs['defaults'][didx]

                if type(default) == bool:
                    stype = bool
                elif type(default) == NoneType:
                    stype = Coerce(str)
                else:
                    stype = Coerce(type(default))
                s[arg] = stype

        # Add reload option to service.running
        if state in ['service.running']:
            s['reload'] =  bool

        schema[state] = Schema(s)

    return schema

def validate_sls(mods, saltenv='base', test=None, queue=False, env=None, **kwargs):

    schema = _getschema()
    ret = {}
    errors = []
    data = __salt__['state.show_sls'](mods, saltenv, test, queue, env, kwargs=kwargs)

    # Errors returned from state
    if type(data) == list:
      return data

    # iterate over ids
    for id, resource in data.items():

        # TODO: include and exclude are lists of states and/or ids, without arguments
        #       we could validate them with their own schema
        if id in ['__include__', '__exclude__']:
             break

        ret[id] = {}

        # iterate over states
        for module, args in resource.items():

            # Ignore dunder dicts
            if module in ['__sls__', '__env__']:
                continue

            # find state name, i.e. cmd.run
            function = [e for e in args if type(e) == str][0]
            state = "%s.%s" % (module, function)

            # check state is valid
            if state not in schema:
                errors.append("%s: %s not available in schema" % (id, state))
                continue

            # iterate over arguments to make sure they're valid according to our schema
            for arg in [e for e in args if type(e) != str]:
                try:
                    schema[state](arg)
                except Exception as e:
                    if e.msg == "extra keys not allowed":
                        errors.append("%s: %s is not a valid argument for %s" % (id, arg.iterkeys().next(), state))
                    else:
                        errors.append("%s %s: Got %s for %s but %s" % (id, state, arg.itervalues().next(), arg.iterkeys().next(), e.msg))
                ret[id][state] = { 'result': True }

    if len(errors) > 0:
       __context__['retcode'] = 1
       return errors
    return ret
