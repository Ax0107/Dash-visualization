import os
import api
import unittest
import tempfile


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, api.server.config['DATABASE'] = tempfile.mkstemp()
        api.server.config['TESTING'] = True
        self.server = api.server.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(api.server.config['DATABASE'])

    def test_redirect_with_no_args(self):
        rv = self.server.get('/dash/api')
        assert b'Redirecting' in rv.data


if __name__ == '__main__':
    unittest.main()
