# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.photoUpload import blueprint
from flask import render_template, request, redirect, url_for
import requests
from jinja2 import TemplateNotFound
from apps import logger, grafanaUrl, FE_url, app_manager_fe
from apps.services.home.routes import get_segment
from apps.services.memcacheManager.routes import getSinglePhotoFromMemcache, getAllPhotosFromCache, invalidateKeyFromMemcache, deleteAllKeysFromDB, getAllPhotosFromDB, putPhotoInMemcache, getPolicyFromDB, changePolicyInDB

@blueprint.route('/index')
# @login_required
def index():
    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
# @login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        if segment=='photos.html':
            return render_template("photoUpload/photos.html", memcache=getAllPhotos()) # needed for Core FE EC2 instance
        if segment=='dashboard.html': 
            return render_template("photoUpload/dashboard.html", grafanaUrl=grafanaUrl) # needed for app-manager EC2 instance
        elif segment=='knownKeys.html':
            return render_template("photoUpload/knownKeys.html", keysFromDB=getDBAllPhotos()) # needed for Core FE EC2 instance
        elif segment=='cache.html':
            return render_template("photoUpload/cache.html", policies=getPolicy())
        return render_template("photoUpload/" + template, segment=segment.replace('.html', ''))

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        logger.error(str(e))
        return render_template('home/page-500.html'), 500


@blueprint.route('/put',methods=['POST', 'PUT'])
def putPhoto():
    # UPLOAD_FOLDER = apps.app_c'/static/assets/public/'
    # ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    key = request.form.get('key') 
    file = request.files['image']
    print(key, file)
    if key and file:
        response = putPhotoInMemcache(key, file)
        
        logger.info('Put request received- ' + str(response))

        return render_template("photoUpload/addPhoto.html", msg=response["msg"])
    elif key:
        cacheData = getSinglePhotoFromMemcache(key)
        if "content" in cacheData:
            return render_template("photoUpload/addPhoto.html", msg="Key exists, please upload a new image", data=cacheData["content"], key=key)
        elif key not in cacheData and "error" in cacheData:
            return render_template("photoUpload/addPhoto.html", msg="Key/Image mismatch, please upload properly")
    else:
            return render_template("photoUpload/addPhoto.html", msg="Key/Image mismatch, please upload properly")
    

# @blueprint.route('/get', defaults={'url_key': None}, methods=['POST'])
@blueprint.route('/get/<url_key>',methods=['GET'])
def getSinglePhoto(url_key):
    key = url_key or request.form.get('key')
    logger.info(request.form)
    cacheData=getSinglePhotoFromMemcache(key)

    logger.info('Get request received for single key- ' + key, str(cacheData))
    logger.info(cacheData)
    logger.info(request.method)
    if "content" in cacheData:
        return render_template("photoUpload/addPhoto.html", data=cacheData["content"], key=key)
    elif "content" not in cacheData and "error" in cacheData:
        return render_template("photoUpload/addPhoto.html", msg=cacheData["error"]["message"], key=key)

@blueprint.route('/getAllCache',methods=['POST'])
def getAllPhotos():
    return getAllPhotosFromCache()["content"]

@blueprint.route('/invalidate_key/<url_key>',methods=['GET', 'POST'])
def invalidateKey(url_key) :
    response = invalidateKeyFromMemcache(url_key)
    logger.info("invalidateKey response: " + str(response))
    
    return redirect(url_for("photoUpload_blueprint.route_template", template="photos.html"))

@blueprint.route('/getAllFromDB',methods=['POST'])
def getDBAllPhotos():
    return getAllPhotosFromDB()["content"]


@blueprint.route('/deleteAllKeys',methods=['GET'])
def deleteAllKeys():
    response = deleteAllKeysFromDB()

    if 'success' in response and response['success']=='true':
        return redirect(url_for("photoUpload_blueprint.route_template", template="knownKeys.html", msg="All Keys are deleted"))


@blueprint.route('/changePolicy',methods=['POST'])
def changePolicy():
    policy = request.form.get("replacement_policy")
    newCapacity = int(request.form.get("capacity"))
    
    response = changePolicyInDB(policy, newCapacity*1024*1024).json()

    print(response)
    if 'success' in response and response['success']=='true':
        return redirect(url_for("photoUpload_blueprint.route_template", template="cache.html"))
        
@blueprint.route('/getCurrentPolicy',methods=['POST'])
def getPolicy():
    return getPolicyFromDB('52.87.212.134')['content']