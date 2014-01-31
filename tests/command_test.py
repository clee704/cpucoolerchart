import sys

import mock
from cpucoolerchart._compat import to_bytes
import cpucoolerchart.command
from cpucoolerchart.command import export, resetdb
from cpucoolerchart.extensions import db
from cpucoolerchart.models import Maker

from .conftest import read_data, fill_data


def test_export(app, capsys):
    with app.app_context():
        db.create_all()
        fill_data()
        export('\t')
        out, err = capsys.readouterr()
        assert to_bytes(out) == read_data('mock.tsv')


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
