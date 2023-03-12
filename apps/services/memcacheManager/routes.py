# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.memcacheManager import blueprint
from flask import request, json, Response
import requests
from apps import logger
from apps.services.cloudWatch.routes import put_metric_data_cw, get_metric_data_cw
from apps.services.nodePartitions.routes import getPartitionRange, getActiveNodes, changeNodes
from apps.services.policyManager.routes import refreshConfiguration
from apps.services.helper import upload_file, removeAllImages

# Upload keys from caches from all the nodes
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
        
        test_getMemcacheSize()
        if 'error' in response:
            response['msg']=response['error']['message']

        print(response)
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
    

# Get keys from caches from all the nodes
@blueprint.route('/key/<url_key>',methods=['GET', 'POST'])
def getSinglePhotoFromMemcache(url_key):
    test_getMemcacheSize()
    key = url_key or request.form.get('key')
    getNodeForKey = getPartitionRange(key)['node_data']

    cacheData = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/key/' + key, data={"key": key}).json()

    cacheStates=[{
            'metricName': 'request_response',
            'dimensionName': 'response_type',
            'dimensionValue': cacheData["cache_status"],
            'value': 1,
            'unit': 'Count',
        }]

    put_metric_data_cw('Cache info', cacheStates)
    if "content" in cacheData:
        return cacheData
    elif "content" not in cacheData and "error" in cacheData:
        return cacheData

# list all caches from all the nodes
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

# list all the keys from database
@blueprint.route('/list_keys',methods=['POST'])
def getAllPhotosFromDB():
    test_getMemcacheSize()
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey['public_ip'])
    return requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/list_keys').json()

# delete everything from database
@blueprint.route('/delete_all',methods=['GET', 'POST'])
def deleteAllKeysFromDB():
    test_getMemcacheSize()
    removeAllImages()
    getNodeForKey = json.loads(getActiveNodes().data)["details"][0]
    print(getNodeForKey)
    response =json.loads(requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/delete_all').content)
    clearCacheFromMemcaches()
    test_getMemcacheSize()
    return response

# configure cache in the database
@blueprint.route('/configure_cache',methods=['POST'])
def changePolicyInDB(policyParam=None, cacheSizeParam=None):
    test_getMemcacheSize()
    currentNodeCount = json.loads(fetchNumberOfNodes().data)['numNodes']
    print(currentNodeCount)
    policy = policyParam or request.args.get("policy")
    if policy and policy=='RR':
        policy='random'
    cacheSize = cacheSizeParam or request.args.get("cacheSize")
    mode = request.args.get('mode')
    numNodes = request.args.get('numNodes')
    if numNodes:
        nodeNum = int(numNodes)
        if currentNodeCount!=nodeNum:
            print('nodeNum' + str(nodeNum))
            print(currentNodeCount)
            print(nodeNum-currentNodeCount)
            changeNodes(nodeNum-currentNodeCount)

    expRatio = request.args.get('expRatio')
    shrinkRatio = request.args.get('shrinkRatio')
    maxMiss = request.args.get('maxMiss')
    minMiss = request.args.get('minMiss')
    
    # response = requests.post(policyManagementUrl+"/refreshConfig", params={'mode': mode, 'numNodes': numNodes, 'cacheSize': cacheSize, 'policy': policy, 'expRatio': expRatio, 'shrinkRatio': shrinkRatio, 'maxMiss': maxMiss, 'minMiss': minMiss})
    print('cacheSize: '  + str(cacheSize))
    response = refreshConfiguration(policy, cacheSize, mode, numNodes, expRatio, shrinkRatio, maxMiss, minMiss)

    print(response)

    if policy and cacheSize:
        print(policy, cacheSize)
        getNodeForKey = json.loads(getActiveNodes().data)["details"]
        print(getNodeForKey)
        for node in getNodeForKey:
            print(node)
            tempData = requests.post('http://' + node['public_ip'] + ':5001/memcache/api/refreshConfig', data={"replacement_policy": policy,"capacity": cacheSize})
            print(tempData)
    # response = requests.post('http://' + getNodeForKey['public_ip'] + ':5001/memcache/api/refreshConfig', data={"replacement_policy": policy,"capacity": newCapacity})
    test_getMemcacheSize()
    return Response(json.dumps(json.loads(response.data)), status=200, mimetype='application/json')
        # ?policy=no_cache&mode=manual&numNodes=3
@blueprint.route('/getCurrentPolicy/<ip>',methods=['POST', 'GET'])
def getPolicyFromDB(ip):
    getNodeForKey = ip
    return requests.get('http://' + getNodeForKey + ':5001/memcache/api/getConfig').json()

@blueprint.route('/getNumNodes', methods=['GET', 'POST'])
def fetchNumberOfNodes():
    return getActiveNodes()

# get miss rate with http://127.0.0.1:5000/api/getRate?rate=miss 
@blueprint.route('/getRate', methods=['GET', 'POST'])
def getRateForRequests():
    rateType = request.args.get('rate')
    getHit=get_metric_data_cw('Cache info', 'request_response', 'response_type', 'hit', 'Sum', 60, 60)['Datapoints']
    getMiss=get_metric_data_cw('Cache info', 'request_response', 'response_type', 'miss', 'Sum', 60, 60)['Datapoints']
    totalHit=0
    totalMiss=0
    if getHit:
        for hitCount in getHit:
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
        # print(cacheInfoFromNodes['memcache_keys_count'])
        # print(cacheInfoFromNodes['memcache_size_mb'])
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
        
        # print(cacheStates)
        response = put_metric_data_cw('cache_states3', cacheStates)
        # print(response)

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

@blueprint.route('/getHitMissInfoFromCW', methods=["GET", "POST"])
def getresponseInfoFromCW():
    getHitCount=get_metric_data_cw('Cache info', 'request_response', 'response_type', 'hit', 'Sum', 60, 24*3600)['Datapoints']
    getMissCount=get_metric_data_cw('Cache info', 'request_response', 'response_type', 'miss', 'Sum', 60, 24*3600)['Datapoints']

    getRequestCount = get_metric_data_cw('Cache info', 'request_response', 'response_type', 'hit', 'Sum', 60, 24*3600)['Datapoints']
    getHitRate = []
    getMissRate = []
    hitLength=len(getRequestCount)
    timestampForHits=[x['Timestamp'] for x in getRequestCount if 'Timestamp' in x.keys()]
    timestampForMiss=[x['Timestamp'] for x in getMissCount if 'Timestamp' in x.keys()]
    print(timestampForHits)
    # while i< hitLength:
    for hit in getHitCount:
        if hit['Timestamp'] not in timestampForMiss:

            getMissCount.append({
                "Sum": 0,
                "Timestamp": hit['Timestamp'],
                "Unit": "Count"
            })

    for miss in getMissCount:
        print(miss['Timestamp'])
        if miss['Timestamp'] not in timestampForHits:
            print('Appending')
            print(miss['Timestamp'])
            print(miss['Sum'])
            getRequestCount.append({
                "Sum": miss['Sum'],
                "Timestamp": miss['Timestamp'],
                "Unit": "Count"
            })

            getHitCount.append({
                "Sum": 0,
                "Timestamp": miss['Timestamp'],
                "Unit": "Count"
            })
        else:
            i=0
            while i< hitLength:
            # for i, hit in enumerate(getMissCount):
                print("i", i)
                print(miss['Timestamp'])
                print(getRequestCount[i]['Timestamp'])
                print("checking starts")
                if miss['Timestamp']==getRequestCount[i]['Timestamp']:
                    print('Summing')
                    print(getRequestCount[i]['Timestamp'])
                    print(getRequestCount[i]['Sum'])
                    print(miss['Sum'])
                    getRequestCount[i] ={
                        "Sum": getRequestCount[i]['Sum']+miss['Sum'],
                        "Timestamp": getRequestCount[i]['Timestamp'],
                        "Unit": "Count"
                    }
                    break
                i=i+1

    for request in getRequestCount:
        for hit in getHitCount:
            if request['Timestamp']==hit['Timestamp']:
                getHitRate.append({
                    "Sum": hit['Sum']/request['Sum'],
                    "Timestamp": request['Timestamp'],
                    "Unit": "Count"
                })
    
    for request in getRequestCount:
        for miss in getMissCount:
            if request['Timestamp']==miss['Timestamp']:
                getMissRate.append({
                    "Sum": miss['Sum']/request['Sum'],
                    "Timestamp": request['Timestamp'],
                    "Unit": "Count"
                })

    return {"hit": getHitCount, "miss":  getMissCount, "total": getRequestCount, "hitRate": getHitRate, "missRate": getMissRate}

@blueprint.route('/getMemcacheInfoFromCW', methods=["GET", "POST"])
def getCacheInfoFromCW():
    getCacheKeysCount=get_metric_data_cw('cache_states3', 'cache_info', 'items_size', 'number_of_items', 'Average', 60, 24*3600)['Datapoints']
    getCacheSizeMb=get_metric_data_cw('cache_states3', 'cache_info', 'items_size', 'total_cache_size', 'Average', 60, 24*3600)['Datapoints']

    return {"count": getCacheKeysCount, "size":  getCacheSizeMb}

@blueprint.route('/getNodeInfoFromCW', methods=["GET", "POST"])
def getNodeInfoFromCW():
    getCacheKeysCount=get_metric_data_cw('Node Info', 'number_of_nodes', 'nodes', 'node_count', 'Average', 60, 24*3600)['Datapoints']

    return {"nodeCount": getCacheKeysCount}

# clear all caches in nodes
@blueprint.route('/clearAll', methods=["GET", "POST"])
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