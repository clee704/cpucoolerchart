import sys

import mock
from cpucoolerchart.command import resetdb
import cpucoolerchart.command
from cpucoolerchart.extensions import db
from cpucoolerchart.models import Maker


def test_resetdb(app):
    _prompt_bool = cpucoolerchart.command.prompt_bool
    cpucoolerchart.command.prompt_bool = mock.Mock(return_value=True)
    with app.app_context():
        db.create_all()
        db.session.add(Maker(name='Intel'))
        db.session.commit()
        resetdb()
        assert Maker.query.all() == []
    cpucoolerchart.command.prompt_bool = _prompt_bool
