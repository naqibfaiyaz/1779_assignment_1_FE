# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from apps import db

from sqlalchemy import Enum, text, ForeignKey

class policyConfig(db.Model):

    __tablename__ = 'policy_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    policy_name = db.Column(db.String(25), Enum('cacheSize', 'policy', 'mode', 'numNodes', 'cacheSize', 'policy', 'expRatio', 'shrinkRatio', 'maxMiss', 'minMiss'), nullable=False, unique=True)
    value = db.Column(db.String(15), nullable=False)
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
            'policy_name': self.policy_name,
            'value': self.value
        }
