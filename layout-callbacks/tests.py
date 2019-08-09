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
        assert rv.status_code == 302

    def test_success_created_figure_trajectory(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=Trajectory&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_bar(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_scatter(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=scatter&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_without_id(self):
        rv = self.server.get('/dash/api?graph_type=scatter&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_two_figure_without_id(self):
        rv = self.server.get('/dash/api?graph_type=scatter&stream=Trajectory&traces=Y')
        rv2 = self.server.get('/dash/api?graph_type=scatter&stream=Trajectory&traces=Z')
        assert rv.status_code == 302 and rv2.status_code == 302

    def test_error_created_figure_non_existed_graph_type(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=qwerty123&stream=Trajectory&traces=X')
        assert rv.status_code == 400

    def test_error_created_figure_some_var_is_none(self):
        rv = self.server.get('/dash/api?figure_id=1&stream=Trajectory&traces=X')
        assert rv.status_code == 400 and b'None' in rv.data

    def test_error_created_figure_some_var_is_none2(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=scatter&stream=Trajectory')
        assert rv.status_code == 400 and b'None' in rv.data

    def test_error_created_figure_some_var_is_none3(self):
        # This may return 302 in the future, because scatter don't need stream.
        rv = self.server.get('/dash/api?figure_id=1&graph_type=scatter&traces=X')
        assert rv.status_code == 400 and b'None' in rv.data

    def test_error_created_figure_some_var_is_none4(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=scatter&stream=Trajectory&traces=')
        assert rv.status_code == 400

    def test_error_created_figure_non_existed_stream(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=pewdiepieprogramming&traces=X')
        assert rv.status_code == 400

    def test_error_created_figure_non_existed_traces(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=Trajectory&traces=lol')
        assert rv.status_code == 400

    def test_error_created_figure_non_existed_traces_list(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=Trajectory&traces=X,Y,hahaha')
        assert rv.status_code == 400

    def test_error_created_figure_non_existed_traces_list2(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=Trajectory&traces=joke,X,Time')
        assert rv.status_code == 400

    def test_error_created_figure_non_existed_traces_list3(self):
        rv = self.server.get('/dash/api?figure_id=1&graph_type=bar&stream=Trajectory&traces=')
        assert rv.status_code == 400



if __name__ == '__main__':
    unittest.main()
