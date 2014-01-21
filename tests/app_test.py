import json

import heroku
import mock

from cpucoolerchart import crawler
from cpucoolerchart.app import app, db, Maker


def setup():
    db.drop_all()
    db.create_all()
    db.session.add(Maker(name='Intel'))
    db.session.commit()


def teardown():
    db.drop_all()


def test_view_makers():
    with app.test_client() as client:
        r = client.get('/makers')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data == {
            "count": 1,
            "items": [{"id": 1, "name": "Intel"}]
        }


def test_view_update():
    heroku.from_key = mock.MagicMock()
    crawler.is_update_needed = mock.Mock(return_value=True)

    app.config['HEROKU_API_KEY'] = '12345678'
    app.config['HEROKU_APP_NAME'] = 'foobar'

    with app.test_client() as client:
        r = client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'process started'
        heroku.from_key.assert_called_with('12345678')
        heroku.from_key.reset_mock()
        assert crawler.is_update_running()

        r = client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'already running'
        assert heroku.from_key.call_count == 0

        crawler.unset_update_running()
        crawler.is_update_needed.return_value = False
        r = client.post('/update')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['msg'] == 'already up to date'
        assert heroku.from_key.call_count == 0

        crawler.is_update_needed.return_value = True
        heroku.from_key.side_effect = RuntimeError
        r = client.post('/update')
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data['msg'] == 'failed'
        assert not crawler.is_update_running()
