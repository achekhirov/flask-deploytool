import git 
import gitlab
import os
import ssh_agent_setup                  #https://github.com/haarcuba/ssh-agent-setup
from deploytool.model import Marketplace, Component, Migration
from deploytool.secret import Secret,Paths

class Repo:
    ssh_agent_setup.setup()
    def __init__(self,component):
        self.name = component
        self.path = f'{Paths.PATH_TO_SOURCE}{self.name}'
        self.repo = git.Repo(self.path)
        self.branch = "humans-release"
        ssh_agent_setup.addKey(Paths.PATH_TO_KEY)
        

    def git_pull(self):
        self.repo.git.checkout(self.branch)
        self.repo.remotes.origin.pull(self.branch)
        return "Component pulled"

class RepoHumans(Repo):
    def __init__(self,component):
        self.name = component
        self.path = f'{Paths.PATH_TO_HELMS}{self.name}'
        self.repo = git.Repo(self.path)
        self.branch = "master"
        ssh_agent_setup.addKey(Paths.PATH_TO_HUMANS_KEY)

    def git_pull(self):
        self.repo.remotes.origin.pull(self.branch)

    def git_push(self):
        if self.name == "marketplace":
            version = Marketplace().version
        elif self.name == "mysql":
            version = Migration().version
            sql_path = "/Users/alexeychekhirov/humansgit/repos/mysql-migration"
            sql_repo = git.Repo(sql_path)
            sql_repo.git.checkout(self.branch)
            sql_repo.git.add("-A")
            sql_repo.git.commit("-m",f"Migrations added in version {version}")
            origin_sql = sql_repo.remote(name='origin')
            origin_sql.push()
        else:
            version = Component(self.name).version
        self.repo.git.checkout(self.branch)
        self.repo.git.add("-A")
        self.repo.git.commit("-m",f"Update chart to {version}")
        origin = self.repo.remote(name='origin')
        origin.push()