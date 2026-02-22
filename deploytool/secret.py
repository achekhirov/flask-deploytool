import keyring

class Secret:
    buildargs = {"GITLAB_USER":"achekhirov","GITLAB_TOKEN":keyring.get_password('gitp2u','achekhirov')}
    pushargs = {"username":"abarkanov","password":keyring.get_password('Docker Nexus','abarkanov')}
    pushhumansargs = {"username":"aleksei.chekhirov@humans.net","GITLAB_HUMANS":keyring.get_password('Gitlab - Humans Token','aleksei.chekhirov@humans.net')}

class Paths:
    PATH_TO_SOURCE = "/Users/alexeychekhirov/Humans/mpp/mpp-p2u/"
    PATH_TO_KEY = "/Users/alexeychekhirov/.ssh/pay2u_gitlab"
    PATH_TO_HUMANS_KEY = "/Users/alexeychekhirov/.ssh/humansgit"
    DOCKER_REGISTRY_PATH="nexus.aws.humans.dc:8082/marketplace/"
    PATH_TO_DB = "/Users/alexeychekhirov/Humans/mpp/mpp-humans/repos/mysql-migration/"
    PATH_TO_HELMS = "/Users/alexeychekhirov/Humans/mpp/mpp-humans/helms/"
    PATH_TO_HUMANS_SOURCE = "/Users/alexeychekhirov/Humans/mpp/mpp-humans/repos/"