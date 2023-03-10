from flask import render_template, redirect, url_for, request
from apps.services.cloudWatch import blueprint
from apps import AWS_ACCESS_KEY, AWS_SECRET_KEY
import boto3, datetime
# from ec2_metadata import ec2_metadata

@blueprint.route('/put',methods=['GET'])
# Display an HTML list of all s3 buckets.
def put_metric_data_cw(namespaceData, data):
    # Let's use Amazon S3
    try:
        cloudWatch = boto3.client('cloudwatch',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name='us-east-1')
        
        for metric in data:
            metrics=[
                {
                    'MetricName': metric['metricName'],
                    'Dimensions': [{
                            'Name': metric['dimensionName'],
                            'Value': metric['dimensionValue']
                        },
                    ],
                    'Timestamp': datetime.datetime.now(),
                    'Value': metric['value'],
                    'Unit': metric['unit']
                },
            ]
            
            # Print out bucket names
            response = cloudWatch.put_metric_data(
                Namespace=namespaceData,
                MetricData=metrics
            )
    except Exception as e:
        print("Error from test_getMemcacheSize: " + str(e))
        return {
            "success": "false",
            "error": { 
                "code": 500,
                "message": str(e)
                }
            }

    return response


@blueprint.route('/get',methods=['GET'])
# Display an HTML list of all s3 buckets.
def get_metric_data_cw(namespace, metricName, dimensions, value):
    # Let's use Amazon S3
    try:
        cloudWatch = boto3.client('cloudwatch',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name='us-east-1')

        # Print out bucket names
        response = cloudWatch.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(seconds=60 * 60),
            EndTime=datetime.datetime.utcnow() - datetime.timedelta(seconds=0 * 60),
            MetricName=metricName,
            Namespace=namespace,  # Unit='Percent',
            Statistics=['Sum'],
            Dimensions=[{'Name': dimensions, 'Value': value}])
    except Exception as e:
        print("Error from test_getMemcacheSize: " + str(e))
        return {
            "success": "false",
            "error": { 
                "code": 500,
                "message": str(e)
                }
            }

    return response