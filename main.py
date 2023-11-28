from pybooru import Danbooru
import config
import utils
import traceback

src_client : Danbooru = None
dst_client : Danbooru = None


def init_clients():
    global src_client
    global dst_client
    src_client = Danbooru(site_name='danbooru', site_url = config.BOORU_SRC_URL,username=config.LOGIN_INFO["SRC"]["USERNAME"], api_key=config.LOGIN_INFO["SRC"]["API_KEY"])
    dst_client = Danbooru(site_name='danbooru', site_url = config.BOORU_DST_URL,username=config.LOGIN_INFO["DST"]["USERNAME"], api_key=config.LOGIN_INFO["DST"]["API_KEY"])
    utils.modify_booru_client_session(src_client, config.REQUEST_SESSION_SETTINGS)
    utils.modify_booru_client_session(dst_client, config.REQUEST_SESSION_SETTINGS)




def print_help():
    print("""
    reinitialize : reinitializes the booru clients if stuff stops working
    quit : exits the program
    help : displays this page
    scrape : scrape multiple posts from a booru
    upload : upload posts from a booru with its post id
    """)
    

def scrape_cb():
    pass



def upload_cb():
    global src_client
    global dst_client
    print("Enter post id/link to upload, enter q to quit...")
    while True:
        inp = input("Input: ")
        if inp == "q":
            return

        post_id = ""
        #parse link
        if "http://" in inp or "https://" in inp:
            #program crashes when u fuck up, cry about it
            idx = inp.find("posts/") + len("posts/")
            cchar : str = inp[idx]
            while cchar.isnumeric() and idx < len(inp):
                cchar : str = inp[idx]
                post_id += cchar
                idx += 1
                
        else:
            post_id = inp
        #grab post and upload
        post_info = src_client.post_show(int(post_id))
        utils.upload_from_post(dst_client, post_info)
        



        
        




command_callbacks = {
    "reinitialize" : init_clients,
    "quit" : exit,
    "help" : print_help,
    "scrape" : scrape_cb,
    "upload" : upload_cb,
}


def main():
    init_clients()
    while True:
        in_cmd = input("Enter command: ")
        try:
            command_callbacks[in_cmd]()   
        except KeyError:
            print("Invalid command!")


    


main()


