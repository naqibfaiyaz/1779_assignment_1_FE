# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.nodePartitions import blueprint
from flask import render_template, request, redirect, url_for, Response
import requests, json
from jinja2 import TemplateNotFound
from apps import logger, api_endpoint, db
from apps.services.home.routes import get_segment
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from sqlalchemy import func

@blueprint.route('/getPartitionForMd5/<key>',methods=['GET'])
# @login_required
def getPartitionRange(key):
    data = db.session.query(nodePartitions, memcacheNodes).join(memcacheNodes).filter(nodePartitions.range_start <= func.md5(key), nodePartitions.range_end >= func.md5(key)).first()

    return {
        'partition_data': data.nodePartitions.serialize,
        'node_data': data.memcacheNodes.serialize
    }


@blueprint.route('/getAllPartitions', methods=['GET'])
# @login_required
def getPartitionAll():
    response = db.session.query(nodePartitions, memcacheNodes).join(memcacheNodes).all()
    print(response)
    allPartitions=[]
    for i in response:
        nodeData = i.nodePartitions.serialize
        nodeData['assigned_instance_status'] = i.memcacheNodes.status
        print(nodeData)
        allPartitions.append(nodeData)
    
    return Response(json.dumps(allPartitions, default=str), status=200, mimetype='application/json')

@blueprint.route('/updateInstance', methods=['POST'])
# @login_required
def updatePartition():
    instanceToAssign = request.form.get('instance_id_to_assign')
    partitionForInstance = request.form.get('partition_id')
    getPartitionDetail = nodePartitions.query.filter_by(id=partitionForInstance).first()
    getPartitionDetail.assigned_instance=instanceToAssign
    db.session.commit()
    
    return nodePartitions.query.filter_by(id=partitionForInstance).first().serialize


@blueprint.route('/getNumNodes',methods=['GET'])
# @login_required
def getActiveNodes():
    response = memcacheNodes.query.filter_by(status='active')
    allActiveNodes = [i.serialize for i in response]
    
    return Response(json.dumps({'success': 'true', 'numNodes': len(allActiveNodes), 'details': allActiveNodes}, default=str), status=200, mimetype='application/json')
     
@blueprint.route('/updateNodeStatus', methods=['POST'])
# @login_required
def updateNodeStatus():
    instanceToChange = request.form.get('instance_to_change')
    status = request.form.get('status')
    getNodeDetail = memcacheNodes.query.filter_by(id=instanceToChange).first()
    getNodeDetail.status=status
    db.session.commit()
    
    return memcacheNodes.query.filter_by(id=instanceToChange).first().serialize
