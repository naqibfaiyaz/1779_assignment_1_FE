# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.services.appManager import blueprint
from apps import db
from flask import render_template, request, redirect, url_for
import requests
from jinja2 import TemplateNotFound
from apps import logger
from apps.services.home.routes import get_segment
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from apps.services.nodePartitions.routes import reassignPartitions

global nodes
nodes=1
global msg
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

@blueprint.route('/show_stats')
def show_stats():
    return render_template('home/index.html', segment='index')

@blueprint.route('/delete_all')
def delete_all():
    return render_template('home/index.html', segment='index')

@blueprint.route('/clear_cache')
def clear_cache():
    return render_template('home/index.html', segment='index')



@blueprint.route('/increase', methods=['POST', 'PUT'])
def increase():
    global nodes
    global msg
    if nodes==8:
        msg='Cannot be more than 8'
        
    else:
        nodes = nodes+1
        msg=nodes
        curr_node=memcacheNodes.query.filter_by(status='inactive').first()
        curr_node.status='active'
        # msg=memcacheNodes.query.filter_by(status='active').count()
        msg=curr_node.id
        db.session.commit()

        #reassignPartitions()


    return render_template('home/index.html', segment='index',msg=msg)


@blueprint.route('/decrease', methods=['POST', 'PUT'])
def decrease():
    global nodes
    global msg
    if nodes==1:
        msg='Cannot be less than 1'
        
    else:
        nodes = nodes-1
        msg=nodes
        curr_node_status=memcacheNodes.query.filter_by(status='active').first()
        msg=curr_node_status
        #curr_node_status.status='inactive'
        reassignPartitions()


    return render_template('home/index.html', segment='index',msg=msg)


@blueprint.route('/auto', methods=['POST', 'PUT'])
def autoModeMemcache1():
    curr_mode='Automatic'
    return render_template('home/index.html', segment='index',curr_mode=curr_mode)
    

@blueprint.route('/manual' , methods=['POST', 'PUT'])
def set_manual_mode():
    curr_mode='Manual'
    return render_template('home/index.html', segment='index',curr_mode=curr_mode)
