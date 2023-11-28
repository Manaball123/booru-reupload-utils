import requests
import pybooru



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

def upload_from_post(client : pybooru.Danbooru, post_info : dict):
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

        client.upload_create(tag_string, source = media_url, rating = post_info["rating"])



