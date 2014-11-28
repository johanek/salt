import os

# import voluptuous

import salt.config
import salt.loader
import salt.utils
from IPython.core.debugger import Tracer

try:
    from salt.utils.validate import voluptuous as V
except ImportError:
    import voluptuous as V

def main():
    '''
    Validate a highstate data structure with a Voluptuous schema

    Performs the following checks:

    * Checks that highstate structure only contains valid keywords
      (declarations & references).
    * Checks that function parameters in function declarations match the
      argspec for that function.
    * TODO: check that *values* given for each function parameter match the
      value specified in the rST documentation for that argument.

    '''
    __opts__ = salt.config.minion_config(
            os.environ.get('SALT_MINION_CONFIG', '/etc/salt/minion'))

    statemods = salt.loader.states(__opts__, {})
    argspecs = salt.utils.argspec_report(statemods)

    specialargs = {
        'name': str,
        'names': list,
        'check_cmd': str,
        'listen': str,
        'listen_in': str,
        'onchanges': str,
        'onchanges_in': str,
        'onfail': str,
        'onfail_in': str,
        'onlyif': str,
        'prereq': str,
        'prereq_in': str,
        'require': str,
        'require_in': str,
        'unless': str,
        'use': str,
        'use_in': str,
        'watch': str,
        'watch_in': str
    }

    # define v schema
    schema = {}
    for k,v in argspecs.iteritems():
        s = specialargs.copy()
        for arg in v['args']:
            s[arg] = [ str, int ]
        schema[k] = V.Schema(s)

    import pprint
    pprint.pprint(schema['webutil.user_exists'].schema)

if __name__ == '__main__':
    main()

# 'user.present': {
#         'args': [ 'name', 'uid', 'gid', 'gid_from_name', 'groups',
#             'optional_groups', 'remove_groups', 'home', 'createhome',
#             'password', 'enforce_password', 'shell', 'unique', 'system',
#             'fullname', 'roomnumber', 'workphone', 'homephone'],
#         'defaults': ( None, None, False, None, None, True, None, True, None,
#             True, None, True, False, None, None, None, None),
#         'kwargs': None,
#         'varargs': None},
