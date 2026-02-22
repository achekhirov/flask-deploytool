import os
import re
import docker
from deploytool.secret import Secret,Paths
from dirsync import sync

path_mapping = {
    "offers-api":"marketplace-api",
    "control-panel":"humans-p2u-marketplace-cp",
    "mysql":"mysql-migration",
    "processing":"humans-p2u-processing",
    "stream-static":"humans-p2u-stream"
}

class Component:    
    def __init__(self,name):
        self.name = name
        
    @property
    def version(self):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/Chart.yaml') as chart_file:
            current_chart_version = re.findall(r'version:[\r\n\s]+(\d.\d.\d{1,})', chart_file.read())[0]
        return current_chart_version

    @property
    def tag(self):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml') as values_file:
            current_image_tag = re.findall(r'tag:[\r\n\s]+(\d.\d.\d{1,})', values_file.read())[0]
        return current_image_tag #returns #### format

    def update_version(self,new_chart_version):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/Chart.yaml') as chart_file:
            chart_data = re.sub(r'\d.\d.\d{1,}',new_chart_version,chart_file.read(),1) 
        with open((f'{Paths.PATH_TO_HELMS}{self.name}/Chart.yaml'),"w") as values_file:
            values_file.write(chart_data)

    def update_tag(self,new_tag_version):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml') as values_file:
            values_data = re.sub(r'\d.\d.\d{1,}', new_tag_version,values_file.read(),1)
        with open((f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml'),"w") as values_file:
            values_file.write(values_data)

    def image_build(self):
        tag = f'{Paths.DOCKER_REGISTRY_PATH}{path_mapping[self.name]}:{self.tag}'
        try:
            docker.from_env().images.build(path=f'{Paths.PATH_TO_SOURCE}{self.name}',tag=tag,buildargs=Secret.buildargs,rm=True)
            return f'Image with tag {self.tag} has been built'
        except docker.errors.BuildError:
            return f'Build of image with {self.tag} unsuccessful'
        except docker.errors.APIError:
            return "Build unsuccessful due to server API error"
        except TypeError:
            return "neither path nor fileobj is specified"
    
    @property
    def images(self):
        tag = f'{Paths.DOCKER_REGISTRY_PATH}{path_mapping[self.name]}:{self.tag}'
        try:
            return docker.from_env().images.get(tag)
        except docker.errors.ImageNotFound:
            return "No Image "
        except docker.errors.DockerException:
            return "Docker Client is not running"
    
    def image_push(self,component):
        try:
            docker.from_env().images.push(f'{Paths.DOCKER_REGISTRY_PATH}{path_mapping[component]}',tag=self.tag,auth_config=Secret.pushargs)
            return f'Image with tag {self.tag} has been pushed to {Paths.DOCKER_REGISTRY_PATH}'
        except docker.errors.APIError:
            return f'Push {self.tag} failed due to an APIError'

class Migration(Component):
    def __init__(self):
        self.name = "mysql"
        
    @property
    def migration(self):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml') as values_file:
            current_image_tag = re.findall(r'mysql-migration:+(\d.\d.\d{1,})', values_file.read())[0]
        return current_image_tag
    
    def update_tag(self,new_tag_version):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml') as values_file:
            values_data = re.sub(r'mysql-migration:+(\d.\d.\d{1,})', f'mysql-migration:{new_tag_version}',values_file.read(),1)    
        with open((f'{Paths.PATH_TO_HELMS}{self.name}/values.yaml'),"w") as values_file:
            values_file.write(values_data)

    def sync_migrations(self):
        sync(f'{Paths.PATH_TO_SOURCE}mysql/sql',f'{Paths.PATH_TO_DB}sql',"sync",options="verbose")
        return "Migrations synchronized"
    
    @property
    def ci(self):
        with open(f'{Paths.PATH_TO_DB}.gitlab-ci.yml') as ci:
            current_ci = re.findall(r'\d.\d.\d{1,}',ci.read())[0]
        return current_ci

    @staticmethod
    def update_ci(new_tag_version):
        with open(f'{Paths.PATH_TO_DB}.gitlab-ci.yml') as ci:
            values_data = re.sub(r'\d.\d.\d{1,}', new_tag_version,ci.read(),1)
        with open(f'{Paths.PATH_TO_DB}.gitlab-ci.yml',"w") as ci:
            ci.write(values_data)

class Marketplace(Component):
    def __init__(self):
        self.components = ["offers-api","control-panel","stream-static","processing","mysql"]
        self.name = "marketplace"
        self.master_components_version = [[component,self.get_components_version(component)] for component in self.components]
        self.change_log = [self.get_change_log(component) for component in self.components if self.get_change_log(component)]
    
    def get_components_version(self,component):
        with open(f'{Paths.PATH_TO_HELMS}{self.name}/Chart.yaml') as chart_file:
            current_chart_version = re.findall(rf'{component}[\r\n\s]+([^\r\n]+)', chart_file.read())[0]
        return current_chart_version #returns version: #### format

    def update_mpp(self,new_chart_version):
        with open(f'{Paths.PATH_TO_HELMS}marketplace/Chart.yaml') as chart_file:
            chart_data_version = re.sub(r'(\d.\d.\d{1,})', new_chart_version, chart_file.read(),2) # flag 2 means only 2 occurence is changed by sub: version and appVersion
        with open((f'{Paths.PATH_TO_HELMS}marketplace/Chart.yaml'), "w") as chart_file:
            chart_file.write(chart_data_version)

    def update_master_components(self):
        for component in self.components:
            current_component_version = f'{component}\n    version: {Component(component).version}' if component != "mysql" else f'{component}\n    version: {Migration().version}'
            with open(f'{Paths.PATH_TO_HELMS}marketplace/Chart.yaml') as chart_file:
                update_component_version = re.sub(rf'{component}[\r\n\s]+([^\r\n]+)',current_component_version,chart_file.read())
            with open((f'{Paths.PATH_TO_HELMS}marketplace/Chart.yaml'),"w") as chart_file:
                chart_file.write(update_component_version)

    def get_change_log(self,component):
        mpp_comp_version = self.get_components_version(component).replace("version: ", "")
        comp_version = Component(component).version if component != "mysql" else Migration().version
        return [component,comp_version] if mpp_comp_version != comp_version else None