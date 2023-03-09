# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import IntegerField
from wtforms import validators
from wtforms.validators import Email, DataRequired

# login and registration


class atuoform(FlaskForm):
    
    Max_miss_threshold = IntegerField('max miss rate threshold', [validators.required()])
    Min_miss_threshold    = IntegerField('min miss rate threshold', [validators.required()])
    ratio_expand = IntegerField('Rate to expand pool', [validators.required()])
    ratio_shrink    = IntegerField('Rate to shrink pool', [validators.required()])


    