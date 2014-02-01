"""
    cpucoolerchart.models
    ~~~~~~~~~~~~~~~~~~~~~

    Defines ORM models to store data persistently.

"""

from flask.ext.sqlalchemy import BaseQuery

from .extensions import db


class BaseModel(db.Model):
    """Extends :class:`db.Model`. All models inherit this base.

    """
    __abstract__ = True

    def _column_names(self):
        return self.__table__.columns.keys()

    def update(self, **kwargs):
        """Updates the current instance. Example:

        .. code-block:: python

            >>> class Person(BaseModel):
            ...    name = db.Column(db.String(100), primary_key=True)
            ...
            >>> person = Person(name='bob')
            >>> person.update(name='john')
            >>> person.name
            'john'

        If all specified values are the same with the current values, no
        assignment occurs so that ``db.session.dirty`` is not changed.

        """
        for name in self._column_names():
            if name not in kwargs:
                continue
            current_value = getattr(self, name)
            new_value = kwargs[name]
            if current_value != new_value:
                setattr(self, name, new_value)

    def as_dict(self):
        """Returns columns as a mapping. Example:

        .. code-block:: python

            >>> class Person(BaseModel):
            ...    name = db.Column(db.String(100), primary_key=True)
            ...    age = db.Column(db.Integer)
            ...
            >>> Person(name='bob', age=24).as_dict()
            {'name': 'bob', 'age': 24}

        """
        return dict((k, getattr(self, k)) for k in self._column_names())

    def __repr__(self):
        values = ', '.join('{0}={1!r}'.format(k, getattr(self, k)) for k
                           in self._column_names())
        return '{model_name}({values})'.format(
            model_name=self.__mapper__.class_.__name__,
            values=values)

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return all(getattr(self, name) == getattr(other, name)
                   for name in self._column_names())

    class Query(BaseQuery):

        def find(self, **kwargs):
            return self.filter_by(**kwargs).scalar()

        def all_as_dict(self):
            return [obj.as_dict() for obj in self.all()]

    query_class = Query


class Maker(BaseModel):
    """Represents a company that makes heatsinks."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)


class Heatsink(BaseModel):
    """Represents a heatsink."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    maker_id = db.Column(db.Integer, db.ForeignKey('maker.id'), nullable=False,
                         index=True)
    width = db.Column(db.Float)
    depth = db.Column(db.Float)
    height = db.Column(db.Float)
    heatsink_type = db.Column(db.String(31), nullable=False)
    weight = db.Column(db.Float)
    danawa_id = db.Column(db.Integer)
    price = db.Column(db.Integer)
    shop_count = db.Column(db.Integer)
    first_seen = db.Column(db.DateTime)
    image_url = db.Column(db.String(511))
    maker = db.relationship('Maker', backref=db.backref('heatsinks',
                            order_by=name.asc(),
                            cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('name', 'maker_id'),)


class FanConfig(BaseModel):
    """Represents a combination of a heatsink and one or more fans."""

    id = db.Column(db.Integer, primary_key=True)
    heatsink_id = db.Column(db.Integer, db.ForeignKey('heatsink.id'),
                            nullable=False, index=True)
    fan_size = db.Column(db.Integer, nullable=False)
    fan_thickness = db.Column(db.Integer, nullable=False)
    fan_count = db.Column(db.Integer, nullable=False)
    heatsink = db.relationship('Heatsink', backref=db.backref('fan_configs',
                               order_by=(fan_size.asc(), fan_thickness.asc(),
                                         fan_count.asc()),
                               cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('heatsink_id', 'fan_size',
                                          'fan_thickness', 'fan_count'),)


class Measurement(BaseModel):
    """Represents a measurement for a specific fan config under a specific
    fan noise and CPU power consumption target.

    """

    id = db.Column(db.Integer, primary_key=True)
    fan_config_id = db.Column(db.Integer, db.ForeignKey('fan_config.id'),
                              nullable=False, index=True)
    noise = db.Column(db.Integer, nullable=False, index=True)
    power = db.Column(db.Integer, nullable=False, index=True)
    noise_actual_min = db.Column(db.Integer)
    noise_actual_max = db.Column(db.Integer)
    rpm_min = db.Column(db.Integer)
    rpm_max = db.Column(db.Integer)
    cpu_temp_delta = db.Column(db.Float, nullable=False, index=True)
    power_temp_delta = db.Column(db.Float, index=True)
    fan_config = db.relationship('FanConfig', backref=db.backref(
        'measurements',
        order_by=(noise.asc(), power.asc()),
        cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('fan_config_id', 'noise', 'power'),)
