
import config
import utils
import traceback
import requests
import urllib3

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
    global src_session
    global dst_session
    #cant be bothered to handle errors here
    page_start_idx = input("Enter start number of pages(leave blank for 1): ")
    page_start_idx = int(page_start_idx) if len(page_start_idx) > 0 else 1
    page_n = input(("Enter number of pages(leave blank for 1): "))
    page_n = int(page_n) if len(page_n) > 0 else 1
    tag_string = input("Enter tag string: ")
    page_range = range(page_start_idx, page_start_idx + page_n)
    print("Scraping pages: " + str(page_range))
    utils.start_concurrent_scrape(page_range, tag_string, src_session, dst_session)
    
    



def upload_cb():
    global src_session
    global dst_session
    print("Enter post id/link to upload, enter q to quit...")
    while True:
        inp = input("Input: ")
        if inp == "q":
            return

        post_id = None
        #grab post and upload
        try:
            if "http://" in inp or "https://" in inp:
                post_id = utils.get_id_from_url(inp)
            else:
                post_id = int(inp)
        except:
            print("Invalid input!")
            continue

        post_info = src_session.get_post(int(post_id))
        utils.upload_from_post(dst_session, post_info, "meta:manually_uploaded")
        



command_callbacks = {
    "reinitialize" : init_clients,
    "quit" : exit,
    "help" : print_help,
    "scrape" : scrape_cb,
    "upload" : upload_cb,
}


def main():
    urllib3.disable_warnings()
    init_clients()

    while True:
        in_cmd = input("Enter command: ")
        if not in_cmd in command_callbacks:
            print("Invalid command!")
            continue
        
        command_callbacks[in_cmd]()   
        


    


main()


