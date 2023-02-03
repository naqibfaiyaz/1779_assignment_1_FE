# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.services.photoUpload import blueprint
from flask import render_template, request, redirect, url_for
import requests
from jinja2 import TemplateNotFound
from apps import logger, api_endpoint
from apps.services.home.routes import get_segment

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
            return render_template("photoUpload/photos.html", memcache=getAllPhotos())
        elif segment=='knownKeys.html':
            return render_template("photoUpload/knownKeys.html", keysFromDB=getDBAllPhotos())
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
    if request.form.get('key') and request.files['image']:
        response = requests.post(api_endpoint + '/upload', files={"file": request.files['image']}, data={"key": request.form.get('key')}).json()
        
        logger.info('Put request received- ' + str(response))

        return render_template("photoUpload/photos.html", msg=response["msg"], memcache=getAllPhotos())
    elif request.form.get('key'):
        key = request.form.get('key')
        cacheData = requests.post(api_endpoint + '/key/' + key, data={"key": key}).json()
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
    cacheData = requests.post(api_endpoint + '/key/' + key, data={"key": key}).json()
    logger.info('Get request received for single key- ' + key, str(cacheData))
    logger.info(cacheData)
    logger.info(request.method)
    if "content" in cacheData:
        return render_template("photoUpload/addPhoto.html", data=cacheData["content"], key=key)
    elif "content" not in cacheData and "error" in cacheData:
        return render_template("photoUpload/addPhoto.html", msg=cacheData["error"]["message"], key=key)

@blueprint.route('/getAllCache',methods=['POST'])
def getAllPhotos():
    return requests.post(api_endpoint + '/list_cache').json()["content"]

@blueprint.route('/invalidate_key/<url_key>',methods=['GET', 'POST'])
def invalidateKey(url_key) :
    response = requests.post(api_endpoint + '/invalidate/' + url_key, data={"key": url_key})
    logger.info("invalidateKey response: " + str(response))
    
    return redirect(url_for("photoUpload_blueprint.route_template", template="photos.html"))

@blueprint.route('/getAllFromDB',methods=['POST'])
def getDBAllPhotos():
    return requests.post(api_endpoint + '/list_keys').json()["content"]


@blueprint.route('/deleteAllKeys',methods=['GET'])
def deleteAllKeys():
    resposne = requests.post(api_endpoint + '/delete_all').json()

    if 'success' in resposne and resposne['success']=='true':
        return redirect(url_for("photoUpload_blueprint.route_template", template="knownKeys.html", msg="All Keys are deleted"))


@blueprint.route('/changePolicy',methods=['POST'])
def changePolicy():
    policy = request.form.get("replacement_policy")
    newCapacity = int(request.form.get("capacity"))
    print(policy, newCapacity)
    resposne = requests.post(api_endpoint + '/refreshConfig', data={"replacement_policy": policy,"capacity": newCapacity*1024*1024}).json()

    if 'success' in resposne and resposne['success']=='true':
        return redirect(url_for("photoUpload_blueprint.route_template", template="cache.html"))
        
@blueprint.route('/getCurrentPolicy',methods=['POST'])
def getPolicy():
    return requests.get(api_endpoint + '/getConfig').json()['content']