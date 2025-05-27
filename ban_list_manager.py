import pandas as pd
import json

BAN_LIST = "conf/ban_list.json"

def add_ban(value):
    with open(BAN_LIST, "r") as f:
        bl = json.load(f)
    list_ = bl["ban_list"]
    list_.append(str(value))
    bl["ban_list"] = list_
    with open(BAN_LIST, "w") as f:
        json.dump(bl, f, indent=4, ensure_ascii=False)

def get_ban_list():
    with open(BAN_LIST, "r") as f:
        bl = json.load(f)
    return bl["ban_list"]

def reset_ban_list():
    with open(BAN_LIST, "r") as f:
        bl = json.load(f)
    list_ = []
    bl["ban_list"] = list_
    with open(BAN_LIST, "w") as f:
        json.dump(bl, f, indent=4, ensure_ascii=False)

def add_csv_as_ban(csv_path):
    df = pd.read_csv(csv_path, sep=";")
    bans = [i for i in df[df.columns[0]].unique().tolist()]
    #bans = bans[:-1] does the to_list() create an useless object " datatype" ??? 

    with open(BAN_LIST, "r") as f:
        bl = json.load(f)
    full_list = bl["ban_list"]

    for ban in bans:
        full_list.append(ban)

    bl["ban_list"] = full_list

    with open(BAN_LIST, "w") as f: 
        json.dump(bl, f, indent=4, ensure_ascii=False)

def add_pattern(pattern):
    with open(BAN_LIST) as f:
        bl = json.load(f)

    patts = bl["ban_pattern"]
    patts.append(rf"{pattern}.*")
    bl["ban_pattern"] = patts

    with open(BAN_LIST, "w") as f:
        json.dump(bl, f, indent=4, ensure_ascii=False)

def get_patt_list():
    with open(BAN_LIST, "r") as f:
        bl = json.load(f)
    return bl["ban_pattern"]
