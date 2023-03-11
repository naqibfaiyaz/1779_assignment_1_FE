# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.nodePartitions import blueprint
from flask import render_template, request, redirect, url_for, Response
import requests, json
from apps import logger, db
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from apps.services.cloudWatch.routes import put_metric_data_cw
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
def updatePartition(node_id=None, partition_id=None):
    instanceToAssign = request.form.get('instance_id_to_assign') or node_id
    partitionForInstance = request.form.get('partition_id') or partition_id
    getPartitionDetail = nodePartitions.query.filter_by(id=partitionForInstance).first()
    getPartitionDetail.assigned_instance=instanceToAssign
    db.session.commit()
    
    return nodePartitions.query.filter_by(id=partitionForInstance).first().serialize


@blueprint.route('/getActiveNodes',methods=['GET'])
# @login_required
def getActiveNodes():
    response = memcacheNodes.query.filter_by(status='active')
    allActiveNodes = [i.serialize for i in response]
    cacheStates=[{
            'metricName': 'number_of_nodes',
            'dimensionName': 'nodes',
            'dimensionValue': 'node_count',
            'value': len(allActiveNodes),
            'unit': 'Count',
        }]

    put_metric_data_cw('Node Info', cacheStates)

    return Response(json.dumps({'success': 'true', 'numNodes': len(allActiveNodes), 'details': allActiveNodes}, default=str), status=200, mimetype='application/json')
     
@blueprint.route('/updateNodeStatus', methods=['POST'])
# @login_required
def updateNodeStatus(instanceId=None, NewStatus=None):
    instanceToChange = instanceId or request.form.get('instance_to_change')
    status = NewStatus or request.form.get('status')
    getNodeDetail = memcacheNodes.query.filter_by(id=instanceToChange).first()
    getNodeDetail.status=status
    db.session.commit()

    # reassignPartitions()
    
    return memcacheNodes.query.filter_by(id=instanceToChange).first().serialize

@blueprint.route('/getAllNodes', methods=['GET'])
# @login_required
def getNodesAll():
    response = db.session.query(memcacheNodes).all()
    allActiveNodes = [i.serialize for i in response]
    
    return Response(json.dumps({'success': 'true', 'numNodes': len(allActiveNodes), 'details': allActiveNodes}, default=str), status=200, mimetype='application/json')

@blueprint.route('/reassignPartitions', methods=['POST'])
def reassignPartitions():

    # get all active nodes
    active_nodes = json.loads(getActiveNodes().data)
    num_nodes = active_nodes['numNodes']
    
    all_nodes = active_nodes['details']

    # enumerate them and assign partitions to them %(#active nodes)
    num_partitions = 16
    for i in range(num_partitions):
        node_to_be_assigned = all_nodes[i % num_nodes]['id']
        updatePartition(node_to_be_assigned, i+1)

    # Waiting until AWS servers are live 
    reassignKeys()

    return getPartitionAll()

@blueprint.route('/reassignKeys', methods=['POST'])
def reassignKeys():

    try:
        # get active keys in memcache
        api_endpoint = getPartitionRange('test')['node_data']['public_ip'] + ':5001'
        keys = requests.post(api_endpoint + '/list_keys').json()["content"]

        for key in keys:

            # get md5 hash for key, determine partition -> instance it will go in
            api_endpoint = getPartitionRange(key)['node_data']['public_ip'] + ':5001'

            # put the key in that instance according to replacement policy
            requests.post(api_endpoint + '/key/' + key, data={"key": key}).json()

        return {"success": 'true'}

    except:
        return {"success": 'false'}
    
@blueprint.route('/changeNodes/<additionalNodeRequired>', methods=['POST', 'GET'])
def changeNodes(additionalNodeRequired):
    allNodes = json.loads(getNodesAll().data)['details']
    # 
    i=0
    print(additionalNodeRequired)
    for node in allNodes:
        if float(additionalNodeRequired)>0 and node['status']=='inactive':
            print(node)
            updateNodeStatus(node['id'], 'active')
            
            i=i+1
        elif float(additionalNodeRequired)<0 and node['status']=='active':
            updateNodeStatus(node['id'], 'inactive')
            
            i=i+1

        
        if i >= int(abs(float(additionalNodeRequired))):
            break
        

    reassignPartitions()

    return json.loads(getActiveNodes().data)