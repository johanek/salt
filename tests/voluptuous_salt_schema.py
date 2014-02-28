import os

# import voluptuous

import salt.config
import salt.loader
import salt.utils

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

    import pprint
    pprint.pprint(argspecs)

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
