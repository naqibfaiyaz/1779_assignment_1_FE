# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.services.UI import blueprint
from flask import render_template, request, redirect, url_for
import requests
from jinja2 import TemplateNotFound
from apps import logger, api_endpoint
from apps.services.home.routes import get_segment
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from nodePartitions.routes import reassignPartitions

nodes = 1
curr_mode='Manual'


@blueprint.route('/index')
# @login_required
def index():
    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
# @login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        
    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        logger.error(str(e))
        return render_template('home/page-500.html'), 500

@blueprint.route('/getCurrentPolicy', methods=['POST'])
def getPolicy():
    return requests.get(api_endpoint + '/getConfig').json()['content']


@blueprint.route('/show_stats')
def show_stats():
    render_template('home/index_.html', segment='index')

@blueprint.route('/delete_all')
def delete_all():
    render_template('home/index_.html', segment='index')

@blueprint.route('/clear_cache')
def clear_cache():
    render_template('home/index_.html', segment='index')



@blueprint.route('/increase', methods=['POST', 'PUT'])
def increase():
    if nodes==8:
        msg='Cannot be more than 8'
        
    else:
        nodes = nodes+1
        msg=nodes
        curr_node=memcacheNodes.query.filter_by(status='active').first()
        curr_node.status='inactive'
        reassignPartitions()


    render_template('home/index_.html', segment='index',msg=msg)


@blueprint.route('/decrease', methods=['POST', 'PUT'])
def decrease():
    if nodes==1:
        msg='Cannot be less than 1'
        
    else:
        nodes = nodes-1
        msg=nodes
        curr_node=memcacheNodes.query.filter_by(status='active').first()
        curr_node.status='inactive'
        reassignPartitions()


    render_template('home/index_.html', segment='index',msg=msg)


@blueprint.route('/automatic', method=['POST', 'PUT'])
def set_auto_mode():
    curr_mode='Automatic'
    if request.form.get('Max_miss_threshold') and request.form.get('Min_miss_threshold') and request.form.get('ratio_shirnk') and request.form.get('ratio_expand'):
        return render_template('home/index_.html', segment='index',curr_mode=curr_mode)
    

@blueprint.route('/manual' , method=['POST', 'PUT'])
def set_manual_mode():
    curr_mode='Manual'
    return render_template('home/index_.html', segment='index',curr_mode=curr_mode)


