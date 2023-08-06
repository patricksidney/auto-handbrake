import sys
import json
import os
import time


def display_splash():
    print("Auto Handbrake")
    print("Version 0.1.0")
    print("By: patricksidney (psidney.com)")
    print("------------------------------------")


def determine_config_file():
    if len(sys.argv) < 2:
        print("No config file specified. Using default.")
        return "default.json"
    else:
        try:
            open(sys.argv[1])
        except IOError:
            print("Config file not found: " + sys.argv[1])
            sys.exit()
        print("Using config file: " + sys.argv[1])
        return sys.argv[1].split('/')[-1]


def validate_config_file(config_file_to_use):
    # read config file into a dict\
    config_file = open('profiles\\configs\\' + config_file_to_use)
    config = json.load(config_file)
    config_file.close()
    # validate config file
    # check for required keys
    required_keys = ["handbrake_path", "handbrake_options", "source_path", "destination_path",
                     "polling_interval", "window_start", "window_end", "new_install", "subfolders", "scheduled", "logging"]
    for key in required_keys:
        if key not in config:
            print("Config file is missing required key: " + key)
            sys.exit()
    return config

    # check for valid values
    # handbrake_path
    if not os.path.isfile(config["handbrake_path"]):
        print("Handbrake path is invalid: " + config["handbrake_path"])
        sys.exit()
    # handbrake_options

    # source_path
    if not os.path.isdir(config["source_path"]):
        print("Source path is invalid: " + config["source_path"])
        sys.exit()

    # destination_path
    if not os.path.isdir(config["destination_path"]):
        print("Destination path is invalid: " + config["destination_path"])
        sys.exit()

    # polling_interval
    if not isinstance(config["polling_interval"], int):
        print("Polling interval is invalid: " + config["polling_interval"])
        sys.exit()

    # window_start
    if not isinstance(config["window_start"], int):
        print("Window start is invalid: " + config["window_start"])
        sys.exit()

    # window_end
    if not isinstance(config["window_end"], int):
        print("Window end is invalid: " + config["window_end"])
        sys.exit()

    # new_install
    if not isinstance(config["new_install"], bool):
        print("New install is invalid: " + config["new_install"])
        sys.exit()

    # subfolders
    if not isinstance(config["subfolders"], bool):
        print("Subfolders is invalid: " + config["subfolders"])
        sys.exit()

    # scheduled
    if not isinstance(config["scheduled"], bool):
        print("Scheduled is invalid: " + config["scheduled"])
        sys.exit()

    return config


def is_in_window(window_start, window_end):
    # get current time
    current_time = time.localtime()
    # get current hour
    current_hour = current_time.tm_hour
    # check if current hour is between window start and window end
    if current_hour >= window_start and current_hour < window_end:
        return True
    else:
        return False


def sleep_until_window(window_start):
    # determine how many minutes until window start
    # get current time
    current_time = time.localtime()
    # get current hour
    current_hour = current_time.tm_hour
    # get current minute
    current_minute = current_time.tm_min
    # determine how many minutes until window start
    minutes_until_window_start = (
        window_start - current_hour) * 60 - current_minute
    print("Sleeping until window start: " +
          str(minutes_until_window_start) + " minutes")
    # sleep until window start
    time.sleep(minutes_until_window_start * 60)


def update_queue(config, config_file_to_use):
    # open completed queue file
    try:
        completed_queue_file = open("profiles\\details\\" + config_file_to_use.replace('.json', '.completed.json'), 'r+')
        # read completed queue file into a dict
        completed_queue = json.load(completed_queue_file)
        # close completed queue file
        completed_queue_file.close()
    except IOError:
        completed_queue_file = open("profiles\\details\\" + config_file_to_use.replace('.json', '.completed.json'), 'w')
        completed_queue = []
        json.dump(completed_queue, completed_queue_file)
        completed_queue_file.close()
    # get list of files in source path, including subfolders if configured
    if config["subfolders"]=="true":
        files = []
        print(config["source_path"])
        for (dirpath, dirnames, filenames) in os.walk(config["source_path"]):
            files.extend(filenames)
            break
        print(f"File count: {len(files)}")
    else:
        files = os.listdir(config["source_path"])

    # remove files that are already in the completed queue
    for file in completed_queue:
        if file in files:
            files.remove(file)

    return files

def logging(config):
    if config["logging"]=="true":
        return "> log.txt"
    else:
        return ""

def encode_item(item, config, config_file_to_use):
    # call handbrake with the handbrake options and item as the source
    # handbrake_path -i item -o destination_path handbrake_options
    sys_command = config["handbrake_path"] + " -i " + os.path.join(config["source_path"], item) + " -o " + os.path.join(config["destination_path"], item) + " " + config["handbrake_options"] + logging(config)
    print("Encoding: " + item)
    print("Command: " + sys_command)
    # making system call and getting results
    result = os.system(sys_command)
    # if successful
    if result == 0:
        print("Encoding successful: " + item)
        return True
    # if not successful
    else:
        print("Encoding failed: " + item)
        return False


def add_to_completed_queue(item, config, config_file_to_use):
    # open completed queue file
    completed_queue_file = open("profiles\\details\\" + config_file_to_use.replace('.json', '.completed.json'), 'r+')
    # read completed queue file into a dict
    completed_queue = json.load(completed_queue_file)
    # close completed queue file
    completed_queue_file.close()

    # add item to completed queue
    completed_queue.append(item)

    # open completed queue file
    completed_queue_file = open("profiles\\details\\" + config_file_to_use.replace('.json', '.completed.json'), 'w')
    # write completed queue file
    json.dump(completed_queue, completed_queue_file)
    # close completed queue file
    completed_queue_file.close()


def main_loop(config, config_file_to_use):

    while True:
        print("Checking for files to encode...")
        # if scheduled, check if in window
        if config["scheduled"]=="true":
            # is it currently between the window start and end?
            if not is_in_window(config["window_start"], config["window_end"]):
                # if not, sleep until window
                sleep_until_window(config["window_start"])
            # if in window
            else:
                # while in window
                while is_in_window(config["window_start"], config["window_end"]):
                    queue = update_queue(config, config_file_to_use)
                    # if no queued items
                    while len(queue) == 0:
                        queue = update_queue(config, config_file_to_use)
                        # sleep for polling interval
                        print(f"Sleeping for {int(config['polling_interval']) * 60} seconds")
                        time.sleep(int(config["polling_interval"]) * 60)
                    # if queued items
                    # encode first item in queue
                    result = encode_item(queue[0], config, config_file_to_use)
                    if result == True:
                        add_to_completed_queue(
                            queue[0], config, config_file_to_use)
        else:
            print(*"Not scheduled, running continuously")
            while True:
                print("Checking for files to encode...")
                queue = update_queue(config, config_file_to_use)
                print(len(queue))
                # if no queued items
                while len(queue) == 0:
                    queue = update_queue(config, config_file_to_use)
                    # sleep for polling interval
                    print(f"Sleeping for {int(config['polling_interval']) * 60} seconds")
                    time.sleep(int(config["polling_interval"]) * 60)
                # if queued items
                # encode first item in queue
                result = encode_item(queue[0], config, config_file_to_use)
                if result == True:
                    add_to_completed_queue(
                        queue[0], config, config_file_to_use)


def main():

    display_splash()

    config_file_to_use = determine_config_file()

    config = validate_config_file(config_file_to_use)

    main_loop(config, config_file_to_use)


if __name__ == "__main__":
    main()
