import unittest

try:
    from salt.utils.validate import voluptuous as V
except ImportError:
    import voluptuous as V

import salt.config

schema = V.Schema({
    V.Required('reactor'): V.Any(None, [dict]),
    V.Required('external_auth'):  V.Any(None, {
        str: {
            str: list,
        },
    }),
}, extra=True)

class TestSchema(unittest.TestCase):
    def test_master_schema(self):
        master_opts = salt.config.client_config('/home/shouse/tmp/venvs/salt/etc/salt/master')
        schema(master_opts)

if __name__ == '__main__':
    unittest.main()
