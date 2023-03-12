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

    # missRate=1

    if missRate > config['maxMiss']:
        if activeNodeCount['numNodes']<8 and int(activeNodeCount['numNodes'])*float(config['expRatio'])<=8:
            NodeAddition = int(activeNodeCount['numNodes'])*float(config['expRatio'])-activeNodeCount['numNodes']
            response = requests.post(nodeManagerUrl + '/changeNodes/' + str(NodeAddition)).json()
        else:
            print(int(activeNodeCount['numNodes']*config['expRatio']))
            response =  {
                "success": "false",
                "msg": "Current node count is " + str(activeNodeCount['numNodes']) + ". Cannot expand further at " + str(config['expRatio']) + " ratio."
            }
    elif missRate < config['minMiss']:
        if activeNodeCount['numNodes']>1 and int(activeNodeCount['numNodes'])*float(config['shrinkRatio'])>=1:
            NodeAddition = int(activeNodeCount['numNodes'])*float(config['shrinkRatio'])-activeNodeCount['numNodes']
            print("addition: " + str(int(activeNodeCount['numNodes'])*float(config['shrinkRatio'])))
            print("active: " + str(activeNodeCount['numNodes']))
            print("addition: " + str(NodeAddition))
            response = requests.get(nodeManagerUrl + '/changeNodes/' + str(NodeAddition)).json()
            print(response)
        else:
            response =  {
                "success": "false",
                "msg": "Current node count is " + str(activeNodeCount['numNodes']) + ". Cannot shrink further at " + str(config['shrinkRatio']) + " ratio."
            }
    else:
        response = {
            "msg": "Nothing to do"
        }
    
    # print(missRate, config, activeNodeCount)

    return response

    # return render_template("s3_examples/list.html",title="s3 Instances",buckets=buckets)
