import requests
import config
import time
import traceback
import queue
import procpool
import functools
import threading
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
        resp_obj = None
        while retry:
            retry = False
            try:
                if method != "GET":
                    resp = self.session.request(method, self.url + endpoint, json=payload, auth=cur_auth, verify=False)
                else:  
                    resp = self.session.request(method, self.url + endpoint, params=payload, auth=cur_auth, verify=False)

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
                #data from POSTing to posts.json returns a html request
                try:
                    resp_obj = resp.json()
                    if "success" in resp_obj:
                        if resp_obj["success"] == False:
                            print("API Call failed. Retrying..")
                            retry = True
                            continue
                except:
                    pass
                    

            except:
                print(traceback.format_exc())
                retry = True
                time.sleep(3)
                print("Unknown error. Retrying after 3s.")
                continue
        assert resp != None
        return resp_obj
    def get_post(self, post_id : int, use_auth : bool = False):
        return self.request(endpoint="/posts/" + str(post_id) + ".json", use_auth=use_auth)

    def query_posts(self, query_tags : str, use_auth : bool = False, num_posts : int = config.SCRAPED_POSTS_PER_PAGE, page_num : int = 1):
        return self.request(use_auth=use_auth, payload={
            "limit" : num_posts,
            "tags" : query_tags,
            "page" : page_num
        })
    def upload_media(self, media_url : str):
        return self.request("POST", True, "/uploads.json", {
            "source" : media_url
        })
        


def get_media_url(post_info : dict) -> str:
    media_asset_info = post_info["media_asset"]["variants"]
    #find original
    for v in media_asset_info:
        if v["type"] == "original":
            return v["url"]


def check_post_valid(post_info : dict) -> bool:
    if post_info["is_banned"]:  
        return False
    return True



def modify_session_attributes(orig_session : requests.Session, attrs : dict) -> requests.Session:
    #no assert to check attribute validity, please dont pass in random shit
    for k in attrs.keys():
        setattr(orig_session, k, attrs[k])
    return orig_session



def annotate_tag_string(tagstring : str, tag_type : str):
    tags = tagstring.split()
    new_str = ""
    for v in tags:
        new_str += tag_type + ":" + v + " "
    return new_str

def create_typed_tagstring(post_info : dict) -> str:
    tag_string = post_info["tag_string_general"] + " "
    tag_string += annotate_tag_string(post_info["tag_string_character"], "character")
    tag_string += annotate_tag_string(post_info["tag_string_copyright"], "copyright")
    tag_string += annotate_tag_string(post_info["tag_string_meta"], "meta")
    return tag_string

def get_id_from_url(url : str) -> int:
    #parse link
    post_id = ""
    #program crashes when u fuck up, cry about it
    idx = url.find("posts/") + len("posts/")
    cchar : str = url[idx]
    while cchar.isnumeric() and idx < len(url):
        cchar : str = url[idx]
        #there 100% is  a   better way but i just fucking cant rn
        if not cchar.isnumeric():
            break
        post_id += cchar
        idx += 1
    return int(post_id)


#MAKE SURE TO CONFIGURE UR API PERMS PROPERLY
def upload_from_post(session : DanbooruSession, post_info : dict, appended_tags : str = ""):
    if not check_post_valid(post_info):
        print("Invalid post. Skipping...")
        return
    #annotate potentially new tags
    
    tag_string = create_typed_tagstring(post_info)
    #TODO: make config 4 this
    tag_string += appended_tags

    media_url = get_media_url(post_info)
    #upload media
    upload_resp = session.upload_media(media_url)
    time.sleep(10)
    #ughhhhh
    upload_complete = False
    while not upload_complete:
        asset_resp = session.request("GET", True, "/uploads/" + str(upload_resp["id"]) + ".json")
        if "status" in asset_resp:
            #status may be error, handle it somehow
            #reupload
            if asset_resp["status"] == "error":
                print("Upload error. Reuploading...")
                upload_resp = session.upload_media(media_url)
                time.sleep(10)
                continue
                    

            if asset_resp["status"] != "completed":
                print("Upload not complete. Retring after 5s.")
                time.sleep(5)
                continue
            
            upload_complete = True
        else:
            print('the fuck??')


    asset_id = asset_resp["upload_media_assets"][0]["id"]
    time.sleep(2)
    session.request("POST", True, "/posts.json", {
            'upload_media_asset_id' : asset_id,
            'rating': post_info["rating"],
            'tag_string': tag_string,
            'is_pending' : False
    })
    print("Uploaded post: " + str(post_info["id"]))

        
class SharedObject:
    def __init__(self, src_session, dst_session) -> None:
        self.queue = queue.Queue()
        self.src_session : DanbooruSession = src_session
        self.dst_session : DanbooruSession = dst_session
        self.more_tasks_available = True

    
        
def worker_proc(shared : SharedObject):
    while not shared.queue.empty() or shared.more_tasks_available:
        try:
            task = shared.queue.get(True, timeout=1)
        except:
            continue

        upload_from_post(shared.dst_session, task, "meta:scraped")
        shared.queue.task_done()
    
def task_fetch_proc(shared : SharedObject, page_range : range, query_string : str):
    for i in page_range:
        posts_data = shared.src_session.query_posts(query_string, page_num=i)
        for v in posts_data:
            shared.queue.put(v)
        time.sleep(1)
    shared.more_tasks_available = False


    


#ZERO process concurrency because fuck you 
def start_concurrent_scrape(page_range : range, query_string : str, src_session, dst_session):
    shared_obj = SharedObject(src_session, dst_session)
    worker_noargs = functools.partial(worker_proc, shared=shared_obj)
    fetcher_noargs = functools.partial(task_fetch_proc, shared=shared_obj, page_range=page_range, query_string=query_string)
    fetcher_thread = threading.Thread(target=fetcher_noargs, args=())
    worker_pool = procpool.ConcurrentThreadPool(config.THREADPOOL_THREAD_N, worker_noargs, ())
    
    fetcher_thread.start()
    worker_pool.execute()
    fetcher_thread.join()


    
    
