from flask import Flask, render_template, request
from deploytool import app
from deploytool.model import Component,Marketplace,Migration
from deploytool.repo import Repo, RepoHumans
from deploytool.releases import Release,db

@app.route('/',methods=["POST","GET"])
@app.route('/home',methods=["GET"])
def index():
    return render_template("index.html")

@app.route('/about',methods=['POST','GET'])
def about():
    api = Component("offers-api")
    cp = Component("control-panel")
    processing = Component("processing")
    stream = Component("stream-static")
    db = Migration()
    mpp = Marketplace()
    if request.method == "POST":
        x = [RepoHumans(component).git_pull() for component in mpp.components]
        RepoHumans(mpp.name).git_pull()
    return render_template("about.html",api=api,cp=cp,processing=processing,stream=stream,db=db,mpp=mpp)

@app.route('/versions/<string:component>',methods=["POST","GET"])
def component_details(component):
    if request.method == "POST":
        component_current = Component(component)
        component_current.update_version(request.form["new_version"])
        component_current.update_tag(request.form["new_tag"])
    component=Component(component)
    return render_template("component_details.html",component=component)

@app.route('/versions/mysql',methods=["POST","GET"])
def mysql_details():
    if request.method == "POST":
        component_current = Migration()
        component_current.update_version(request.form["new_version"])
        component_current.update_tag(request.form["new_tag"])
        component_current.update_ci(request.form["new_tag"])
    component=Migration()
    return render_template("mysql_details.html",component=component)

@app.route('/versions/master',methods=['POST','GET'])
def master():
    change_log = Marketplace().change_log
    if request.method == "POST":
        if request.form.get("update"):
            mpp_new = Marketplace()
            mpp_new.update_mpp(request.form["master_version"])
            desc = request.form["desc"]
            release = Release(mpp=mpp_new.version,change_log=change_log,desc=desc)
            db.session.add(release)
            db.session.commit()
            mpp_new.update_master_components()
        elif request.form.get("push"):
            push_mpp = RepoHumans("marketplace")
            push_mpp.git_push()
            changed = db.session.query(Release.change_log).order_by(Release.date.desc()).first()[0]
            push_charts = [RepoHumans(component[0]).git_push() for component in changed if component is not None]
    mpp = Marketplace()
    return render_template("master.html",mpp=mpp,change_log=change_log)

@app.route('/build/<string:component>',methods=['POST','GET'])
def build_component(component):
    component = Component(component)
    if request.method == "POST":
        if request.form.get("build"):
            status = component.image_build()
        elif request.form.get("push"):
            status = component.image_push(component.name)
        elif request.form.get("pull"):
            repo = Repo(component.name)
            status = repo.git_pull()
    else:
        status = None
    return render_template("build.html",component=component,status=status)

@app.route('/build/mysql',methods=["GET","POST"])
def sync_mysql():
    db = Migration()
    if request.method == "POST":
        if request.form.get("sync"):
            status = db.sync_migrations()
        elif request.form.get("pull"):
            Repo(db.name).git_pull()
            status = "DB Migrations have been pulled"
        elif request.form.get("push"):
            RepoHumans(db.name).git_push()
            status = "DB Migrations pushed"
    else:
        status = None
    return render_template("mysql.html",status=status)

@app.route('/releases',methods=["GET","POST"])
def releases():
    if request.method == "POST":
        release_id = request.form.get("erase")
        release = Release.query.get(release_id)
        db.session.delete(release)
        db.session.commit()
    releases = Release.query.order_by(Release.date.desc()).all()
    return render_template("releases.html",releases=releases)