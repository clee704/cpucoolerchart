from flask.ext.sqlalchemy import BaseQuery

from .extensions import db


class Model(db.Model):
  __abstract__ = True

  def _column_names(self):
    return self.__table__.columns.keys()

  def update(self, **kwargs):
    for name in self._column_names():
      if name not in kwargs:
        continue
      current_value = getattr(self, name)
      new_value = kwargs[name]
      if current_value != new_value:
        setattr(self, name, new_value)

  def as_dict(self):
    return {k: getattr(self, k) for k in self._column_names()}

  def __repr__(self):
    values = ', '.join('{0}={1}'.format(k, repr(getattr(self, k))) for k in self._column_names())
    return '{model_name}({values})'.format(model_name=self.__mapper__.class_.__name__,
        values=values)

  class Query(BaseQuery):

    def find(self, **kwargs):
      return self.filter_by(**kwargs).scalar()

    def all_as_dict(self):
      return [obj.as_dict() for obj in self.all()]

  query_class = Query


class Maker(Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False, unique=True, index=True)


class Heatsink(Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), nullable=False, index=True)
  maker_id = db.Column(db.Integer, db.ForeignKey('maker.id'), nullable=False, index=True)
  width = db.Column(db.Float)
  depth = db.Column(db.Float)
  height = db.Column(db.Float)
  heatsink_type = db.Column(db.String(31), nullable=False)
  weight = db.Column(db.Float)
  maker = db.relationship('Maker', backref=db.backref('heatsinks', order_by=name.asc()))

  __table_args__ = (db.UniqueConstraint('name', 'maker_id'),)


class FanConfig(Model):
  id = db.Column(db.Integer, primary_key=True)
  heatsink_id = db.Column(db.Integer, db.ForeignKey('heatsink.id'), nullable=False, index=True)
  fan_size = db.Column(db.Integer, nullable=False)
  fan_thickness = db.Column(db.Integer, nullable=False)
  fan_count = db.Column(db.Integer, nullable=False)
  heatsink = db.relationship('Heatsink', backref=db.backref('fan_configs',
      order_by=(fan_size.asc(), fan_thickness.asc(), fan_count.asc())))

  __table_args__ = (db.UniqueConstraint('heatsink_id', 'fan_size', 'fan_thickness', 'fan_count'),)


class Measurement(Model):
  id = db.Column(db.Integer, primary_key=True)
  fan_config_id = db.Column(db.Integer, db.ForeignKey('fan_config.id'), nullable=False, index=True)
  noise = db.Column(db.Integer, nullable=False, index=True)
  power = db.Column(db.Integer, nullable=False, index=True)
  noise_actual_min = db.Column(db.Integer)
  noise_actual_max = db.Column(db.Integer)
  rpm_min = db.Column(db.Integer)
  rpm_max = db.Column(db.Integer)
  cpu_temp_delta = db.Column(db.Float, nullable=False, index=True)
  power_temp_delta = db.Column(db.Float, index=True)
  fan_config = db.relationship('FanConfig', backref=db.backref('measurements',
      order_by=(noise.asc(), power.asc())))

  __table_args__ = (db.UniqueConstraint('fan_config_id', 'noise', 'power'),)
