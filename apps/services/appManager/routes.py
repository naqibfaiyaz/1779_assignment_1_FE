# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.services.appManager import blueprint
from apps import db, backendUrl
from flask import render_template, request, redirect, url_for
import requests
from jinja2 import TemplateNotFound
from apps import logger
from apps.services.home.routes import get_segment
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from apps.services.nodePartitions.routes import reassignPartitions

global curr_mode
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

@blueprint.route('/clear_cache')
def clear_cache():
    response = requests.post(backendUrl + '/clearAll').json()['msg']
    return render_template('home/index.html', segment='index', msg=response)



@blueprint.route('/increase', methods=['POST', 'PUT'])
def increase():
    
    nodes=memcacheNodes.query.filter_by(status='active').count()
    if nodes==8:
        msg='Cannot be more than 8'
        
    else:
        nodes = nodes-1
        curr_node=memcacheNodes.query.filter_by(status='active').first()
        curr_node.status='inactive'
        db.session.commit()

        #reassignPartitions()
        #flash('Record was successfully added')
        


    return render_template('home/index.html', segment='index',msg=msg)


@blueprint.route('/decrease', methods=['POST', 'PUT'])
def decrease():
    
    nodes=memcacheNodes.query.filter_by(status='active').count()
    
    if nodes==1:
        msg='Cannot be less than 1'
        
    else:
        nodes = nodes-1
        curr_node=memcacheNodes.query.filter_by(status='active').first()
        curr_node.status='inactive'
        db.session.commit()
        #msg=nodes
        # curr_node_st/

    return render_template('home/index.html', segment='index',msg=nodes)


@blueprint.route('/automatic', methods=['POST', 'PUT'])
def autoModeMemcache1():
    curr_mode='Automatic'
    return render_template('home/index.html', segment='index',curr_mode=curr_mode)
    

@blueprint.route('/manual' , methods=['POST', 'PUT'])
def set_manual_mode():
    curr_mode='Manual'
    return render_template('home/index.html', segment='index',curr_mode=curr_mode)
