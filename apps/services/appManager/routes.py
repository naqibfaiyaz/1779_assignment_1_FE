# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.services.appManager import blueprint
from apps import db, backendUrl
from flask import render_template, request, json
import requests
from jinja2 import TemplateNotFound
from apps import logger, nodeManagerUrl
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

# @blueprint.route('/show_stats')
# def show_stats():

#     return render_template('home/index.html', segment='index')

@blueprint.route('/clear_cache')
def clear_cache():
    response = requests.post(backendUrl + '/clearAll').json()['msg']
    return render_template('home/index.html', segment='index', cache_msg=response)

@blueprint.route('/increase', methods=['POST', 'PUT'])
def increase():
    
    nodes= requests.post(backendUrl + '/getNumNodes').json()['numNodes']
    if nodes>=8:
        msg='Cannot be more than 8'
        
    else:
        # nodes = nodes+1
    #     curr_node=memcacheNodes.query.filter_by(status='inactive').first()
    #     curr_node.status='active'
        # msg=nodes
    #     reassignPartitions()
        
    #     db.session.commit()
        response = requests.post(nodeManagerUrl + '/changeNodes/1').json()
        msg=response['numNodes']
        #flash('Record was successfully added')
        


    return render_template('home/index.html', segment='index',msg=msg)


@blueprint.route('/decrease', methods=['POST', 'PUT'])
def decrease():
    
    nodes=requests.post(backendUrl + '/getNumNodes').json()['numNodes']
    
    if nodes<=1:
        msg='Cannot be less than 1'
        
    else:
        # nodes = nodes-1
        # curr_node=memcacheNodes.query.filter_by(status='active').first()
        # curr_node.status='inactive'
        
        # reassignPartitions()
        
        # db.session.commit()
        response = requests.post(nodeManagerUrl + '/changeNodes/-1').json()
        msg=response['numNodes']
        #msg=nodes
        # curr_node_st/

    return render_template('home/index.html', segment='index',msg=msg)


@blueprint.route('/config', methods=['POST', 'PUT'])
def autoModeMemcache1():
    policy = request.form.get("replacement_policy")
    cacheSize = request.form.get("capacity")
    mode = request.form.get("mode")
    expRatio = request.form.get('ratio_expand') 
    shrinkRatio = request.form.get('ratio_shrink')
    maxMiss = request.form.get('Max_miss_threshold')
    minMiss = request.form.get('Min_miss_threshold')
    response = requests.post(backendUrl + '/configure_cache',
                             params={
                'policy': policy or None,
                'cacheSize': cacheSize or None,
                'mode': mode or None,
                'maxMiss': maxMiss or None,
                'minMiss': minMiss or None,
                'expRatio': expRatio or None,
                'shrinkRatio': shrinkRatio or None,
        })
    curr_config=json.loads(response.content)
    return render_template('home/index.html', segment='index',curr_config=json.dumps(curr_config))
    

# @blueprint.route('/mode' , methods=['POST', 'PUT'])
# def set_manual_mode():
#     curr_mode = requests.post(backendUrl + '/configure_cache',
#                              params={'mode': request.form.get('mode')}).json()['mode']
#     return render_template('home/index.html', segment='index',curr_mode=curr_mode)
