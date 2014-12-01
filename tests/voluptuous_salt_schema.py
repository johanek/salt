import sys
import os

# import voluptuous

import pprint
import re
import salt.config
import salt.loader
import salt.utils
from IPython.core.debugger import Tracer

try:
    from salt.utils.validate import voluptuous as V
except ImportError:
    import voluptuous as V

def main(file):
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
        'listen': list,
        'listen_in': list,
        'onchanges': list,
        'onchanges_in': list,
        'onfail': list,
        'onfail_in': list,
        'onlyif': str,
        'prereq': list,
        'prereq_in': list,
        'require': list,
        'require_in': list,
        'unless': str,
        'use': list,
        'use_in': list,
        'watch': list,
        'watch_in': list
    }

    # define v schema
    # this doesn't seem to include everything - pkg.installed???
    schema = {}
    for k,v in argspecs.iteritems():
        s = specialargs.copy()
        for arg in v['args']:
            s[arg] = str
        schema[k] = V.Schema(s)

    # Render state
    renderers = salt.loader.render(__opts__, {})
    try:
        content = renderers['jinja'](file).read()
        data = renderers['yaml'](content)
    except salt.exceptions.SaltRenderError as error:
        output("%s: %s" % (file, error))

    # iterate over states
    # TODO: make sure variable names match what salt calls them
    #       add include, exclude to schema
    prog = re.compile(r'.*\.')
    for id, v in data.items():
        if id in ['include', 'exclude']:
            break

        # iterate over states
        for state, options in v.items():
            # find function name, i.e. cmd.run
            match = prog.match(state)
            if match:
                resource = state
            else:
                resource = "%s.%s" % (state, options.pop(0))

            # check function exists in scema
            # TODO: don't nest ifs here - break out of loop if this fails
            if resource in schema:

                # iterate over arguments to make sure they're valid according to our schema
                for opt in options:
                    try:
                        schema[resource](opt)
                    except Exception as e:
                        output("%f: %s %s: Got %s for %s but %s" % (file, id, resource, opt.itervalues().next(), opt.iterkeys().next(), e.msg))
            else:
                print "%s: %s not part of schema" % (file, resource)

#    pprint.pprint(schema['webutil.user_exists'].schema)

def output(message):
  pprint.pprint(message)

if __name__ == '__main__':
    for file in sys.argv[1:]:
        main(file)

# 'user.present': {
#         'args': [ 'name', 'uid', 'gid', 'gid_from_name', 'groups',
#             'optional_groups', 'remove_groups', 'home', 'createhome',
#             'password', 'enforce_password', 'shell', 'unique', 'system',
#             'fullname', 'roomnumber', 'workphone', 'homephone'],
#         'defaults': ( None, None, False, None, None, True, None, True, None,
#             True, None, True, False, None, None, None, None),
#         'kwargs': None,
#         'varargs': None},
