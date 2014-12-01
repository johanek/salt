import sys
import os

# import voluptuous

import pprint
import re
import salt.config
import salt.loader
import salt.utils
from types import *

try:
  from IPython.core.debugger import Tracer
except:
  print "no ipython"

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
    __salt__ = salt.loader.minion_mods(__opts__)
    __opts__['grains'] = salt.loader.grains(__opts__)

    # Statemods doesn't seen to return all the state modules????
    # https://gist.github.com/johanek/459fa02df48511566a26
    statemods = salt.loader.states(__opts__, __salt__)
    argspecs = salt.utils.argspec_report(statemods)

    specialargs = {
        'name': V.Coerce(str),
        'names': list,
        'check_cmd': str,
        'listen': list,
        'listen_in': list,
        'onchanges': list,
        'onchanges_in': list,
        'onfail': list,
        'onfail_in': list,
        'onlyif': V.Coerce(str),
        'prereq': list,
        'prereq_in': list,
        'require': list,
        'require_in': list,
        'unless': V.Coerce(str),
        'use': list,
        'use_in': list,
        'watch': list,
        'watch_in': list,
        'formatter': str
    }

    # define voluptuous schema
    schema = {}
    for state,specs in argspecs.iteritems():
        s = specialargs.copy()
        for idx, arg in enumerate(specs['args']):
            try:
                default = specs['defaults'][idx]
            except:
                default = 'nodefault'
            if type(default) == bool:
                stype = bool
            elif type(default) == NoneType:
                stype = V.Coerce(str)
            else:
                stype = V.Coerce(type(default))
            s[arg] = stype
        schema[state] = V.Schema(s)

    # Render state file
    renderers = salt.loader.render(__opts__, __salt__)
    try:
        content = renderers['jinja'](file).read()
        data = renderers['yaml'](content)
    except salt.exceptions.SaltRenderError as error:
        output("%s: %s" % (file, error))
        return

    # iterate over states
    # TODO: add include, exclude to schema
    #       handle context, defaults better
    prog = re.compile(r'.*\.')
    for id, resource in data.items():
        if id in ['include', 'exclude']:
            break

        # iterate over states
        for module, args in resource.items():
            # find state name, i.e. cmd.run
            match = prog.match(module)
            if match:
                state = module
            else:
                state = "%s.%s" % (module, args.pop(0))

            # check function exists in scema
            if state not in schema:
                output("%s: %s not part of schema" % (file, state))
                break

            # iterate over arguments to make sure they're valid according to our schema
            for arg in args:
                if arg.iterkeys().next() in [ 'context', 'defaults' ]:
                    break
                try:
                    schema[state](arg)
                except Exception as e:
                    output("%s: %s %s: Got %s for %s but %s" % (file, id, state, arg.itervalues().next(), arg.iterkeys().next(), e.msg))

def output(message):
  pprint.pprint(message)

if __name__ == '__main__':
    for file in sys.argv[1:]:
        main(file)
