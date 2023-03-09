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
    
    Max_miss_threshold = IntegerField('Max_miss_threshold', [validators.required()])
    Min_miss_threshold    = IntegerField('Min_miss_threshold', [validators.required()])
    ratio_expand = IntegerField('ratio_expand', [validators.required()])
    ratio_shrink    = IntegerField('ratio_shrink', [validators.required()])


    