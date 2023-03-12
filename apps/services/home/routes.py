# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.home import blueprint
from flask import render_template, request, json, redirect
# from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.services.nodePartitions.models import nodePartitions, memcacheNodes
from apps.services.memcacheManager.routes import changePolicyInDB
import boto3
from apps import AWS_ACCESS_KEY, AWS_SECRET_KEY, db, app_manager_fe


@blueprint.route('/')
# @login_required
def RedirectIndex():
    ec2 = boto3.client('ec2',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name='us-east-1')
    
    instances = ec2.describe_instances(
        Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'memcache',
            ]
        },
    ])

    newMemcacheNodes=[]
    if memcacheNodes.query.count()==0:
        for instance in instances['Reservations']:
            for node in instance['Instances']:
                if node['State']['Name']=='running':
                    instanceId = node['InstanceId']
                    instancePrivateIp = node['PrivateIpAddress']
                    instancePublicIp = node['PublicIpAddress']
                    newMemcacheNodes.append(memcacheNodes(Instance_id = instanceId,
                            private_ip = instancePrivateIp, public_ip= instancePublicIp, status='active'))
            db.session.add_all(newMemcacheNodes)   
            db.session.commit()
    
    if nodePartitions.query.count()==0:
        newNodePartitions=[
            nodePartitions(range_start = '00000000000000000000000000000000', range_end = '0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '10000000000000000000000000000000', range_end = '1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '20000000000000000000000000000000', range_end = '2FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '30000000000000000000000000000000', range_end = '3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '40000000000000000000000000000000', range_end = '4FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '50000000000000000000000000000000', range_end = '5FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '60000000000000000000000000000000', range_end = '6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '70000000000000000000000000000000', range_end = '7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '80000000000000000000000000000000', range_end = '8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = '90000000000000000000000000000000', range_end = '9FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'A0000000000000000000000000000000', range_end = 'AFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'B0000000000000000000000000000000', range_end = 'BFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'C0000000000000000000000000000000', range_end = 'CFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'D0000000000000000000000000000000', range_end = 'DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'E0000000000000000000000000000000', range_end = 'EFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'),
            nodePartitions(range_start = 'F0000000000000000000000000000000', range_end = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
            ]
        db.session.add_all(newNodePartitions)   
        db.session.commit()

    changePolicyInDB('LRU', 10)

    return index()

@blueprint.route('/index')
# @login_required
def index():
    return redirect(app_manager_fe + '/index', code=302) # required for core BE

@blueprint.route('/<template>')
# @login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("photoUpload/" + template, segment=segment.replace('.html', ''))

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
