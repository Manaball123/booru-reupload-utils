import requests
import pybooru
import config
import time
import traceback

#TODO: inherit requests.Session
class DanbooruSession():
    def __init__(self, url : str = "https://danbooru.donmai.org", auth : dict = None, session : requests.Session = requests.Session()):
        self.url : str = url
        self.auth : dict = auth
        self.session : requests.Session = session
    
    def request(self, method : str = "GET", use_auth : bool = False, endpoint = "/posts.json", payload : dict = None):
        retry = True
        cur_auth = (self.auth["USERNAME"], self.auth["API_KEY"]) if use_auth and self.auth != None else None
        resp = None
        while retry:
            retry = False
            try:
                resp = self.session.request(method, self.url + endpoint, json=payload, auth=cur_auth, verify=False)
                status_code = resp.status_code
                #500 Internal Server Error: A database timeout, or some unknown error occurred on the server
                #502 Bad Gateway: Server cannot currently handle the request, try again later (returned during heavy load)
                #503 Service Unavailable: Server cannot currently handle the request, try again later (returned during downbooru)
                if status_code == 500 or status_code == 502 or status_code == 503:
                    time.sleep(1)
                    retry = True
                    print("Server error. Retrying after 1s.")
                    continue
                #429 User Throttled: User is throttled, try again later (see help:users for API limits)
                if status_code == 429:
                    time.sleep(3)
                    retry = True
                    print("API Throttled. Retrying after 3s.")
                    continue
            except:
                print(traceback.format_exc())
                retry = True
                time.sleep(3)
                print("Unknown error. Retrying after 3s.")
                continue
        assert resp != None
        return resp.json()

    


def modify_session_attributes(orig_session : requests.Session, attrs : dict) -> requests.Session:
    #no assert to check attribute validity, please dont pass in random shit
    for k in attrs.keys():
        setattr(orig_session, k, attrs[k])
    return orig_session


def modify_booru_client_session(client : pybooru.Danbooru, attrs : dict) -> pybooru.Danbooru:
    modify_session_attributes(client.client, attrs)
    return client



def annotate_tag_string(tagstring : str, tag_type : str):
    tags = tagstring.split()
    new_str = ""
    for v in tags:
        new_str += tag_type + ":" + v + " "
    return new_str



def upload_from_post(session : DanbooruSession, post_info : dict):
        #annotate potentially new tags
        tag_string = post_info["tag_string_general"] + " "
        tag_string += annotate_tag_string(post_info["tag_string_character"], "character")
        tag_string += annotate_tag_string(post_info["tag_string_copyright"], "copyright")
        tag_string += annotate_tag_string(post_info["tag_string_meta"], "meta")

        #TODO: make config 4 this
        tag_string += "meta:manually_uploaded"

        media_asset_info = post_info["media_asset"]["variants"]
        media_url = ""
        #find original
        for v in media_asset_info:
            if v["type"] == "original":
                media_url = v["url"]
        #upload media
        #refactor this ugly shit
        upload_resp = session.request("POST", True, "/uploads.json", {
            "source" : media_url
        })
        #ughhhhh
        asset_resp = session.request("GET", True, "/uploads/" + str(upload_resp["id"]) + ".json")
        asset_id = asset_resp["upload_media_assets"][0]["id"]
        time.sleep(2)
        session.request("POST", True, "/posts.json", {
                'upload_media_asset_id' : asset_id,
                'rating': post_info["rating"],
                'tag_string': tag_string,
                'is_pending' : False
        })

        



