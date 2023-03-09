# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.memcacheManager import blueprint
from flask import request, json, Response
import requests
from apps import logger, policyManagementUrl
from apps.services.cloudWatch.routes import put_metric_data_cw
from apps.services.nodePartitions.routes import getPartitionRange, getActiveNodes
from apps.services.helper import upload_file, removeAllImages

@blueprint.route('/upload',methods=['POST', 'PUT'])
def putPhotoInMemcache(url_key=None, file=None):
    # UPLOAD_FOLDER = apps.app_c'/static/assets/public/'
    # ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    
    key = url_key or request.form.get('key')
    fileData = file or request.files['file']
    print(key, fileData)
    if key and fileData:
        getNodeForKey = getPartitionRange(key)['node_data']
        print(getNodeForKey)
        image_path = upload_file(fileData)
        response = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/upload', data={"key": key, "image_path": image_path}).json()
        
        logger.info('Put request received- ' + str(response))

        return response
    elif key:
        getNodeForKey = getPartitionRange(key)['node_data']
        cacheData = getSinglePhotoFromMemcache(key)
        if "content" in cacheData:
            return cacheData
        elif key not in cacheData and "error" in cacheData:
            return cacheData
    else:
            return {"Key/Image mismatch, please upload properly"}
    

# @blueprint.route('/get', defaults={'url_key': None}, methods=['POST'])
@blueprint.route('/key/<url_key>',methods=['GET', 'POST'])
def getSinglePhotoFromMemcache(url_key):
    key = url_key or request.form.get('key')
    getNodeForKey = getPartitionRange(key)['node_data']

    cacheData = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/key/' + key, data={"key": key}).json()

    cacheStates=[{
            'metricName': 'cache_response',
            'dimensionName': 'hit_miss',
            'dimensionValue': cacheData["cache_status"],
            'value': 1,
            'unit': 'Count',
        }]

    put_metric_data_cw('Cache Response2', cacheStates)
    if "content" in cacheData:
        return cacheData
    elif "content" not in cacheData and "error" in cacheData:
        return cacheData

@blueprint.route('/list_cache',methods=['POST'])
def getAllPhotosFromCache():
    getNodeForKey = json.loads(getActiveNodes().data)["details"]

    allCache={'content':{},'keys':[], 'success': None}

    for node in getNodeForKey:
        allCacheFromNode= requests.post("http://" + node['public_ip'] + ':5001/memcache/api/list_cache').json()
        print(node['Instance_id'], node['public_ip'])
        print(allCacheFromNode['content'])
        for keys in allCacheFromNode['content']:
            if keys!='key':
                allCache['content'][keys]=allCacheFromNode['content'][keys]
    allCache['keys']=list(allCache['content'].keys())
    allCache['success']='true'
        # print(allCacheFromNode['content'])
    
        # print(allCacheFromNode)
    print(allCache)
        # need to accumulate all the cache
    return allCache

@blueprint.route('/invalidate_key/<url_key>',methods=['GET', 'POST'])
def invalidateKeyFromMemcache(url_key):
    getNodeForKey = getPartitionRange(url_key)['node_data']
    response = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/invalidate/' + url_key, data={"key": url_key})
    logger.info("invalidateKey response: " + str(response))
    
    return response

@blueprint.route('/list_keys',methods=['POST'])
def getAllPhotosFromDB():
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey['public_ip'])
    return requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/list_keys').json()


@blueprint.route('/delete_all',methods=['GET', 'POST'])
def deleteAllKeysFromDB():
    removeAllImages()
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey)
    response =json.loads(requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/delete_all').content)

    return response


@blueprint.route('/configure_cache',methods=['POST'])
def changePolicyInDB(policyParam=None, cacheSizeParam=None):
    policy = policyParam or request.args.get("policy")
    if policy and policy=='RR':
        policy='random'
    cacheSize = cacheSizeParam or request.args.get("cacheSize")
    mode = request.args.get('mode'), 
    numNodes = request.args.get('numNodes'), 
    expRatio = request.args.get('expRatio'), 
    shrinkRatio = request.args.get('shrinkRatio'), 
    maxMiss = request.args.get('maxMiss'), 
    minMiss = request.args.get('minMiss')
    
    response = requests.post(policyManagementUrl+"/refreshConfig", params={'mode': mode, 'numNodes': numNodes, 'cacheSize': cacheSize, 'policy': policy, 'expRatio': expRatio, 'shrinkRatio': shrinkRatio, 'maxMiss': maxMiss, 'minMiss': minMiss})

    print(response)

    if policy and cacheSize:
        print(policy, cacheSize)
        getNodeForKey = json.loads(getActiveNodes().data)["details"]
        print(getNodeForKey)
        for node in getNodeForKey:
            print(node)
            tempData = requests.post('http://' + node['public_ip'] + ':5001/memcache/api/refreshConfig', data={"replacement_policy": policy,"capacity": cacheSize*1024*1024})
            print(tempData)
    # response = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/refreshConfig', data={"replacement_policy": policy,"capacity": newCapacity})

    return Response(json.dumps(json.loads(response.content)), status=200, mimetype='application/json')
        # ?policy=no_cache&mode=manual&numNodes=3
@blueprint.route('/getCurrentPolicy/<ip>',methods=['POST', 'GET'])
def getPolicyFromDB(ip):
    getNodeForKey = ip
    return requests.get('http://' + getNodeForKey + ':5001/memcache/api/getConfig').json()

@blueprint.route('/getNumNodes', methods=['GET', 'POST'])
def fetchNumberOfNodes():
    return getActiveNodes()

# @blueprint.route('/api/getMemcacheSize', methods={"GET"})
# def test_getMemcacheSize():
#     try:
#         cacheStates=[{
#             'metricName': 'number_of_items',
#             'dimensionName': 'number_of_items',
#             'dimensionValue': 'cacheItems',
#             'value': len(memcache),
#             'unit': 'Count',
#         },{
#             'metricName': 'total_cache_size',
#             'dimensionName': 'total_cache_size',
#             'dimensionValue': 'cacheSize',
#             'value': asizeof.asizeof(memcache)/1024,
#             'unit': 'Kilobytes',
#         }]

#         print(cacheStates[0])
#         response = put_metric_data_cw('cache_states2', cacheStates)
#         print(response)

#         return Response(json.dumps({
#             'success': 'true',
#             'data': {
#                 'number_of_items': cacheStates[0],
#                 'total_cache_size': cacheStates[1]
#         }}), status=200, mimetype='application/json')

#     except Exception as e:
#         logging.error("Error from test_getMemcacheSize: " + str(e))
#         Response(json.dumps({
#             "success": "false",
#             "error": { 
#                 "code": 500,
#                 "message": str(e)
#                 }
#             }), status=400, mimetype='application/json')
