import json 

CONF = "conf/conf.json"
DEFAULT = "conf/default_conf.json"

def get(target):
    with open(CONF, "r") as file:
        conf = json.load(file)
        return conf[target]
    

def set(target, value):
    with open(CONF, "r", encoding="utf-8") as file:
        conf = json.load(file)

    conf[target] = value

    with open(CONF, "w", encoding="utf-8") as file:
        json.dump(conf, file, indent=4, ensure_ascii=False)

def set_to_default():
    with open(DEFAULT, "r") as d:
        default = json.load(d)

    with open(CONF, "w") as file:
        json.dump(default, file, indent=4, ensure_ascii=False)