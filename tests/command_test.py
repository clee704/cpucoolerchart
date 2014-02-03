import sys

from mock import patch, Mock

from cpucoolerchart._compat import to_bytes
from cpucoolerchart.command import runworker, resetdb, export
import cpucoolerchart.command
from cpucoolerchart.crawler import update_data
from cpucoolerchart.extensions import update_queue
from cpucoolerchart.models import Maker, Measurement

from .conftest import read_file, fill_data


def test_runworker(db):
    update_queue.enqueue_call(update_data, result_ttl=0)
    runworker(burst=True)
    assert Maker.query.count() == 12
    assert Measurement.query.count() == 290
    assert Maker.query.get(1) == Maker(id=1, name='AMD')


@patch('cpucoolerchart.command.prompt_bool', autospec=True)
def test_resetdb(prompt_bool, db):
    prompt_bool.return_value = True
    db.session.add(Maker(name='Intel'))
    db.session.commit()
    resetdb()
    assert Maker.query.all() == []


def test_export(db, capsys):
    fill_data()
    export('\t')
    out, err = capsys.readouterr()
    assert to_bytes(out) == read_file('mock.tsv')
