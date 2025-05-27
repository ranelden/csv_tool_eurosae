import json

MAIL_JSON = 'conf/mail.json'

def csv_as_list(path):
    with open(MAIL_JSON) as f:
        mp = json.load(f)

    mp["path"] = path

    with open(MAIL_JSON, "w") as f:
        json.dump(mp, f, indent=4, ensure_ascii=False)
    

