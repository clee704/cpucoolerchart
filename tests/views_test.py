import json

import mock
from cpucoolerchart import crawler
from cpucoolerchart.app import create_app
from cpucoolerchart.extensions import db
from cpucoolerchart.models import Maker
import cpucoolerchart.views


class TestViews(object):

    def setup(self):
        self.app = create_app({'CACHE_TYPE': 'simple'})
        self.app.testing = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        db.session.add(Maker(name='Intel'))
        db.session.commit()

    def teardown(self):
        db.session.close()
        db.drop_all()
        db.get_engine(self.app).dispose()
        self.ctx.pop()

    def test_view_makers(self):
        r = self.client.get('/makers')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data == {
            "count": 1,
            "items": [{"id": 1, "name": "Intel"}]
        }

    def test_view_update(self):
        heroku = cpucoolerchart.views.heroku = mock.Mock()
        heroku.from_key = mock.MagicMock()
        crawler.is_update_needed = mock.Mock(return_value=True)

        self.app.config['HEROKU_API_KEY'] = '12345678'
        self.app.config['HEROKU_APP_NAME'] = 'foobar'

        r = self.client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'process started'
        heroku.from_key.assert_called_with('12345678')
        heroku.from_key.reset_mock()
        assert crawler.is_update_running()

        r = self.client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'already running'
        assert heroku.from_key.call_count == 0

        crawler.unset_update_running()
        crawler.is_update_needed.return_value = False
        r = self.client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'already up to date'
        assert heroku.from_key.call_count == 0

        crawler.is_update_needed.return_value = True
        heroku.from_key.side_effect = RuntimeError
        r = self.client.post('/update')
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data['msg'] == 'failed'
        assert not crawler.is_update_running()
