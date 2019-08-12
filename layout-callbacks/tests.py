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
        rv = self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=Trajectory&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_bar(self):
        rv = self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_scatter(self):
        rv = self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_figure_without_id(self):
        rv = self.server.get('/dash/api?graph_type=scatter&uuid=test&stream=Trajectory&traces=X')
        assert rv.status_code == 302

    def test_success_created_two_figure_without_id(self):
        rv = self.server.get('/dash/api?graph_type=scatter&uuid=test&stream=Trajectory&traces=Y')
        rv2 = self.server.get('/dash/api?graph_type=scatter&uuid=test&stream=Trajectory&traces=Z')
        assert rv.status_code == 302 and rv2.status_code == 302

    def test_error_created_figure_non_existed_graph_type(self):
        rv = self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=qwerty123&stream=Trajectory&traces=X')
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

    def test_success_change_style_scatter(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 302

    def test_success_change_style_bar(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        self.test_success_created_figure_scatter()
        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 302

    def test_error_change_style_scatter_none_trace(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_scatter_non_existing_trace(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=500'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_scatter_non_existing_figure(self):
        rv = self.server.get('/dash/api/optional?figure_id=100098&uuid=test'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Does not have figure' in rv.data and b'for user' in rv.data

    def test_error_change_style_scatter_non_existing_figure_for_user(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=supertestuser220'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Does not have figure' in rv.data and b'for user' in rv.data

    def test_error_change_style_bar_non_existing_trace(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=500'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_bar_non_existing_figure(self):
        rv = self.server.get('/dash/api/optional?figure_id=100098&uuid=test'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Does not have figure' in rv.data and b'for user' in rv.data

    def test_error_change_style_bar_non_existing_figure_for_user(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=supertestuser220'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Does not have figure' in rv.data and b'for user' in rv.data

    def test_error_change_style_scatter_line_color_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=supertestuser220'
                             '&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_scatter_marker_color_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=supertestuser220'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_scatter_line_width_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        self.test_success_created_figure_scatter()
        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_scatter_marker_size_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        self.test_success_created_figure_scatter()
        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)')
        assert rv.status_code == 400

    def test_error_change_style_scatter_line_color_incorrect_format(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        self.test_success_created_figure_scatter()
        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_scatter_marker_color_incorrect_format(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_scatter_line_color_incorrect_format2(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=1,1,1,2&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_scatter_marker_color_incorrect_format2(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=1,1,1,2&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_scatter_line_color_incorrect_format3(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1&line_width=10&marker_color=rgba(1,1,1,2)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_scatter_line_color_incorrect_format4(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=scatter&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rykr(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,2)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_bar_marker_color_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=supertestuser220'
                             '&marker_size=1')
        assert rv.status_code == 400

    def test_error_change_style_bar_marker_size_is_none(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        self.test_success_created_figure_bar()
        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)')
        assert rv.status_code == 400

    def test_success_change_style_bar_ignore_line_color_incorrect_format(self):
        # Создаём фигуру
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=rgba(1,1,1)&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 302

    def test_error_change_style_bar_ignore_line_color_incorrect_format2(self):
        # Создаём фигуру с id １
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0'
                             '&line_color=1,1,1,2&line_width=10&marker_color=rgba(1,1,1,1)&marker_size=1')
        assert rv.status_code == 302

    def test_error_change_style_bar_marker_color_incorrect_format(self):
        # Создаём фигуру с id
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0&graph_type=bar'
                             '&line_width=10&marker_color=rg(1,1,1)&marker_size=1')
        print(rv.status_code)
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data

    def test_error_change_style_bar_marker_color_incorrect_format2(self):
        # Создаём фигуру с id
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0&graph_type=bar'
                             '&line_color=1,2,3,4&line_width=10&marker_color=1,23,1,1&marker_size=1')
        print(rv.status_code)
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data and b'1,23,1,1' in rv.data

    def test_error_change_style_bar_marker_color_incorrect_format3(self):
        # Создаём фигуру с id
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0&graph_type=bar'
                             '&line_color=1,2,3,4&line_width=10&marker_color=rdgc(1,2,3,4)&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data and b'1,2,3,4' in rv.data

    def test_error_change_style_bar_marker_color_incorrect_format4(self):
        # Создаём фигуру с id
        self.server.get('/dash/api?figure_id=1&uuid=test&graph_type=bar&stream=Trajectory&traces=X')

        rv = self.server.get('/dash/api/optional?figure_id=1&uuid=test&trace_id=0&graph_type=bar'
                             '&line_color=1,2,3,4&line_width=10&marker_color=rqgc(1,2,3,4&marker_size=1')
        assert rv.status_code == 400 and b'Correct format: rbga(1,1,1,1)' in rv.data and b'1,2,3,4' in rv.data




if __name__ == '__main__':
    unittest.main()
