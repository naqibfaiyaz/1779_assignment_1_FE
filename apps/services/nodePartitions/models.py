# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from apps import db

from sqlalchemy import Enum, text, ForeignKey

class memcacheNodes(db.Model):

    __tablename__ = 'memcache_nodes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Instance_id = db.Column(db.String(30), unique=True, nullable=False)
    private_ip = db.Column(db.String(15), unique=True, nullable=False)
    public_ip = db.Column(db.String(15), unique=True, nullable=False)
    status = db.Column(Enum('active','inactive'))
    created_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'Instance_id': self.Instance_id,
            'private_ip': self.private_ip,
            'public_ip': self.public_ip,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class nodePartitions(db.Model):

    __tablename__ = 'node_partitions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    range_start = db.Column(db.String(32), unique=True, nullable=False)
    range_end = db.Column(db.String(32), unique=True, nullable=False)
    assigned_instance = db.Column(db.Integer, db.ForeignKey('memcache_nodes.id'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'assigned_instance': self.assigned_instance,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
