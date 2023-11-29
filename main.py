
import config
import utils
import traceback
import requests

dst_session : utils.DanbooruSession = None
src_session : utils.DanbooruSession = None

def init_clients():
    global src_session
    global dst_session
    src_session = utils.DanbooruSession(url = config.BOORU_SRC_URL, auth=config.LOGIN_INFO["SRC"], session=utils.modify_session_attributes(requests.Session(), config.REQUEST_SESSION_SETTINGS))
    dst_session = utils.DanbooruSession(url = config.BOORU_DST_URL, auth=config.LOGIN_INFO["DST"], session=utils.modify_session_attributes(requests.Session(), config.REQUEST_SESSION_SETTINGS))




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
    global src_session
    global dst_session
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
                #there 100% is  a   better way but i just fucking cant rn
                if not cchar.isnumeric():
                    break
                post_id += cchar
                idx += 1
            
                
        else:
            post_id = inp
        #grab post and upload
        try:
            int(post_id)
        except:
            print("Invalid input!")
            continue
        post_info = src_session.get_post(int(post_id))
        utils.upload_from_post(dst_session, post_info)
        print("Uploaded! ")
        



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
        if not in_cmd in command_callbacks:
            print("Invalid command!")
            continue
        
        command_callbacks[in_cmd]()   
        


    


main()


