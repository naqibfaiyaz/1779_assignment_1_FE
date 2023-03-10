# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.memcacheManager import blueprint
from flask import request, json, Response
import requests
from apps import logger, policyManagementUrl
from apps.services.cloudWatch.routes import put_metric_data_cw, get_metric_data_cw
from apps.services.nodePartitions.routes import getPartitionRange, getActiveNodes
from apps.services.helper import upload_file, removeAllImages

@blueprint.route('/upload',methods=['POST', 'PUT'])
def putPhotoInMemcache(url_key=None, file=None):
    test_getMemcacheSize()
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
        test_getMemcacheSize()
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
    test_getMemcacheSize()
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
    test_getMemcacheSize()
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
    test_getMemcacheSize()
    getNodeForKey = getPartitionRange(url_key)['node_data']
    response = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/invalidate/' + url_key, data={"key": url_key})
    logger.info("invalidateKey response: " + str(response))
    
    return response

@blueprint.route('/list_keys',methods=['POST'])
def getAllPhotosFromDB():
    test_getMemcacheSize()
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey['public_ip'])
    return requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/list_keys').json()


@blueprint.route('/delete_all',methods=['GET', 'POST'])
def deleteAllKeysFromDB():
    test_getMemcacheSize()
    removeAllImages()
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey)
    response =json.loads(requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/delete_all').content)
    test_getMemcacheSize()
    return response


@blueprint.route('/configure_cache',methods=['POST'])
def changePolicyInDB(policyParam=None, cacheSizeParam=None):
    test_getMemcacheSize()
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
    test_getMemcacheSize()
    return Response(json.dumps(json.loads(response.content)), status=200, mimetype='application/json')
        # ?policy=no_cache&mode=manual&numNodes=3
@blueprint.route('/getCurrentPolicy/<ip>',methods=['POST', 'GET'])
def getPolicyFromDB(ip):
    getNodeForKey = ip
    return requests.get('http://' + getNodeForKey + ':5001/memcache/api/getConfig').json()

@blueprint.route('/getNumNodes', methods=['GET', 'POST'])
def fetchNumberOfNodes():
    return getActiveNodes()

@blueprint.route('/getRate', methods=['GET', 'POST'])
def getRateForRequests():
    rateType = request.args.get('rate')
    getHit=get_metric_data_cw('Cache Response2', 'cache_response', 'hit_miss', 'hit', 'Sum')['Datapoints']
    getMiss=get_metric_data_cw('Cache Response2', 'cache_response', 'hit_miss', 'miss', 'Sum')['Datapoints']
    totalHit=0
    totalMiss=0
    if getHit:
        for hitCount in getMiss:
            totalHit = totalHit + int(hitCount['Sum'])
    else: 
        totalHit=0
    if getMiss:
        for missCount in getMiss:
            totalMiss = totalMiss + int(missCount['Sum'])
    else: 
        totalMiss=0
    
    totalResponse = totalHit+totalMiss

    if rateType=='miss':
        if totalResponse>0:
            rate = totalMiss/totalResponse
            response = {
                "success": "true",
                "rate": rateType,
                "value": rate,
                "hit": totalHit,
                "miss": totalMiss,

            }
        else:
            rate = 0
            response = {
                "success": "true",
                "rate": rateType,
                "value": rate,
                "hit": totalHit,
                "miss": totalMiss,
            }
    elif rateType=='hit':
        if totalResponse>0:
            rate = totalHit/totalResponse
            response = {
                "success": "true",
                "rate": rateType,
                "value": rate,
                "hit": totalHit,
                "miss": totalMiss,
            }
        else:
            rate = 0
            response = {
                "success": "true",
                "rate": rateType,
                "value": rate,
                "hit": totalHit,
                "miss": totalMiss,
            }
    else: 
        return Response(json.dumps("rate type is missing"), status=400, mimetype='application/json')

    return Response(json.dumps(response), status=200, mimetype='application/json')

@blueprint.route('/getMemcacheSize', methods=["GET", "POST"])
def test_getMemcacheSize():
    getNodeForKey = json.loads(getActiveNodes().data)["details"]

    allCacheKeysCount=0
    allCacheSizeMb=0
    for node in getNodeForKey:
        cacheInfoFromNodes= requests.post("http://" + node['public_ip'] + ':5001/memcache/api/getCacheData').json()
        # cacheInfoFromNodes = requests.post('http://127.0.0.1:5001/memcache/api/getCacheData').json()
        print(cacheInfoFromNodes)
        allCacheKeysCount=allCacheKeysCount+int(cacheInfoFromNodes['memcache_keys_count'])
        allCacheSizeMb=allCacheSizeMb+float(cacheInfoFromNodes['memcache_size_mb'])
        print(cacheInfoFromNodes['memcache_keys_count'])
        print(cacheInfoFromNodes['memcache_size_mb'])
        # for keys in allCacheFromNode['content']:
        #     if keys!='key':
        #         allCache['content'][keys]=allCacheFromNode['content'][keys]
    print(allCacheKeysCount, allCacheSizeMb)

    try:
        cacheStates=[{
            'metricName': 'cache_info',
            'dimensionName': 'items_size',
            'dimensionValue': 'number_of_items',
            'value': allCacheKeysCount,
            'unit': 'Count',
        },{
            'metricName': 'cache_info',
            'dimensionName': 'items_size',
            'dimensionValue': 'total_cache_size',
            'value': allCacheSizeMb,
            'unit': 'Megabytes',
        }]
        
        print(cacheStates)
        response = put_metric_data_cw('cache_states3', cacheStates)
        print(response)

        return Response(json.dumps({
            'success': 'true',
            'data': {
                'number_of_items': allCacheKeysCount,
                'total_cache_size': allCacheSizeMb
        }}), status=200, mimetype='application/json')

    except Exception as e:
        logger.error("Error from test_getMemcacheSize: " + str(e))
        Response(json.dumps({
            "success": "false",
            "error": { 
                "code": 500,
                "message": str(e)
                }
            }), status=400, mimetype='application/json')

@blueprint.route('/getMemcacheInfoFromCW', methods=["GET", "POST"])
def getCacheInfoFromCW():
    getCacheKeysCount=get_metric_data_cw('cache_states3', 'cache_info', 'items_size', 'number_of_items', 'Average')['Datapoints']
    getCacheSizeMb=get_metric_data_cw('cache_states3', 'cache_info', 'items_size', 'total_cache_size', 'Average')['Datapoints']

    return {"count": getCacheKeysCount, "size":  getCacheSizeMb}


@blueprint.route('/clearCache', methods=["GET", "POST"])
def clearCacheFromMemcaches():
    getNodeForKey = json.loads(getActiveNodes().data)["details"]

    successCount=0
    for node in getNodeForKey:
        print(node['public_ip'])
        response = requests.post("http://" + node['public_ip'] + ':5001/memcache/api/clearAll').json()
        print(response)
        if response['success']:
            successCount=successCount+1
        # response = requests.post('http://127.0.0.1:5001/memcache/api/clearAll').json()
    
    if successCount==len(getNodeForKey):
        return {
            "success": "true",
            "msg": "Cache cleared from all nodes"
        }
    else:
        return {
            "success": "false",
            "msg": "Could not clear all caches"
        }