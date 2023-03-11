from apps.services.autoScaler import blueprint
from flask import request
import requests
from apps import backendUrl, policyManagementUrl, nodeManagerUrl
import boto3

@blueprint.route('/execute',methods=['GET', 'POST'])
# Display an HTML list of all s3 buckets.
def autoScalerFunction():
    # Let's use Amazon S3
    missRate = requests.post(backendUrl + '/getRate?rate=miss').json()['value']
    config = requests.post(policyManagementUrl + '/getCurrentConfig').json()
    activeNodeCount = requests.post(backendUrl + '/getNumNodes').json()

    if missRate > config['maxMiss']:
        if activeNodeCount['numNodes']<8 and int(activeNodeCount['numNodes'])*float(config['expRatio'])<=8:
            response = increaseNode(int(activeNodeCount['numNodes'])*float(config['expRatio'])-activeNodeCount['numNodes'])
        else:
            print(int(activeNodeCount['numNodes']*config['expRatio']))
            response =  {
                "success": "false",
                "msg": "Current node count is " + str(activeNodeCount['numNodes']) + ". Cannot expand further at " + str(config['expRatio']) + " ratio."
            }
    elif missRate < config['minMiss']:
        if activeNodeCount['numNodes']>1 and int(activeNodeCount['numNodes'])*float(config['shrinkRatio'])>=1:
            response = decreaseNode(activeNodeCount['numNodes']-int(activeNodeCount['numNodes'])*float(config['shrinkRatio']))
        else:
            response =  {
                "success": "false",
                "msg": "Current node count is " + str(activeNodeCount['numNodes']) + ". Cannot shrink further at " + str(config['shrinkRatio']) + " ratio."
            }
    else:
        response = {
            "msg": "Nothing to do"
        }
    
    print(missRate, config, activeNodeCount)

    return response

    # return render_template("s3_examples/list.html",title="s3 Instances",buckets=buckets)

def increaseNode(additionalNodeRequired):
    allNodes = requests.get(nodeManagerUrl + '/getAllNodes').json()['details']
    # 
    i=0
    for node in allNodes:
        if node['status']=='inactive':
            print(node)
            requests.post(nodeManagerUrl + '/updateNodeStatus', data={'instance_to_change': node['id'], 'status': 'active'}).json()
            i=i+1
        
        if i >= int(additionalNodeRequired):
            break

    requests.post(nodeManagerUrl + '/reassignPartitions')

    return requests.post(backendUrl + '/getNumNodes').json()

def decreaseNode(additionalNodeRequired):
    allNodes = requests.get(nodeManagerUrl + '/getAllNodes').json()['details']
    
    i=0
    for node in allNodes:
        if node['status']=='active':
            print(node)
            requests.post(nodeManagerUrl + '/updateNodeStatus', data={'instance_to_change': node['id'], 'status': 'inactive'}).json()
            i=i+1
        
        if i >= int(additionalNodeRequired):
            break

    requests.post(nodeManagerUrl + '/reassignPartitions')

    return requests.post(backendUrl + '/getNumNodes').json()