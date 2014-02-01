from cpucoolerchart.extensions import db
from cpucoolerchart.models import Base


class Person(Base):
    name = db.Column(db.String(100), primary_key=True)
    age = db.Column(db.Integer)


def test_base_update(app):
    with app.app_context():
        db.create_all()
        person = Person(name='John')
        db.session.add(person)
        db.session.commit()
        person.update(name='John')
        assert not db.session.dirty
        person.update(name='Smith')
        assert db.session.dirty
        assert person.name == 'Smith'


def test_base_repr(app):
    with app.app_context():
        db.create_all()
        assert (repr(Person(name='John', age=24)) ==
                "Person(name='John', age=24)")


def test_base_query_find(app):
    with app.app_context():
        db.create_all()
        person = Person(name='John')
        db.session.add(person)
        db.session.commit()
        assert Person.query.find(name='John') == person
