# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.policyManager import blueprint
from flask import render_template, request, redirect, url_for, Response
import requests, json
from jinja2 import TemplateNotFound
from apps import logger, db
from apps.services.home.routes import get_segment
from apps.services.policyManager.models import policyConfig
from sqlalchemy import func


@blueprint.route('/refreshConfig', methods=["POST"])
def refreshConfiguration():
    # test_getMemcacheSize()
    if request.args.get("policy") and request.args.get("policy")=='no_cache':
        capacity=0
    elif request.args.get("cacheSize"):
        capacity = int(request.args.get("cacheSize"))*1024*1024
    else:
        capacity = None

    allPolicies = {
        "policy": request.args.get("policy"),
        "cacheSize": capacity,
        "mode": request.args.get('mode'), 
        "numNodes":  request.args.get('numNodes'), 
        "expRatio": request.args.get('expRatio'), 
        "shrinkRatio": request.args.get('shrinkRatio'), 
        "maxMiss":  request.args.get('maxMiss'), 
        "minMiss": request.args.get('minMiss')
    }

    print(allPolicies)
    for rule in allPolicies:
        if allPolicies[rule] is not None:
            current=policyConfig.query.filter_by(policy_name=rule).first()
            if current:
                current.value=allPolicies[rule]
            else:
                newPolicy = policyConfig(policy_name = rule,
                        value = allPolicies[rule])
                db.session.add(newPolicy)  
            db.session.commit()

    return getConfigAll()


@blueprint.route('/getCurrentConfig', methods=["POST"])
def getConfigAll():
    currentPolicy=db.session.query(policyConfig).all()
    updatedPolicy=[i.serialize for i in currentPolicy]
    
    if updatedPolicy:
        response = {
                "success": 'true',
                "policy": None,
                "cacheSize": None,
                "mode": None, 
                "numNodes":  None, 
                "expRatio": None, 
                "shrinkRatio": None, 
                "maxMiss":  None, 
                "minMiss": None
            }

    for policy in updatedPolicy:
        if policy['policy_name']=='numNodes' or policy['policy_name']=='cacheSize':
            response[policy['policy_name']] = int(policy['value'])
        elif policy['policy_name']=='maxMiss' or policy['policy_name']=='minMiss':
            response[policy['policy_name']] = float(policy['value'])
        else:
            response[policy['policy_name']] = policy['value']

    return Response(json.dumps(response), status=200, mimetype='application/json')