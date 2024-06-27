#
# Copy images from one directory as they appear in it
# Place them on a directory intended to host a website
# At carefully chosen intervals regenerate the index.html etc
# using imageindex to produce the index.html etc
# The latter operation is expensive iand we avoid doing it
# too frequently and when files are still moving


import signal
import os
import sys

import multiprocessing
from multiprocessing import Queue
from multiprocessing import Process
import queue
from datetime import datetime, timedelta
from time import sleep
import inotify
import inotify.adapters
import psutil

remove_boring = True

if remove_boring:
    sys.path.insert(0, "/home/embed/intrusion")
    import yolo

# Attempt orderly shutdown


def handler(signum):
    """Catch termination signal so I can terminate child"""
    signame = signal.Signals(signum).name
    print("Caught signal", signame)

    for p in multiprocessing.active_children():
        p.terminate()

    sys.exit()


#


def act(q, path, filename):
    """On an inotify event, queue up the filename
    of what has just arrived"""
    debug = False

    if debug:
        print(path + filename)
    q.put(path + filename)


#
#   Setup inotify
#


def initiate_watch(q, path):
    """Setup watching for files arrivving in the source directory"""
    i = inotify.adapters.InotifyTree(path)

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if "IN_CLOSE_WRITE" in type_names:
            act(q, path, filename)


# Cheap... if yolo not involved


def transfer(path, filename, website):
    """Transfer a file named in the queue to the website"""
    debug = False

    lifeforms = set(["person", "dog"])

    #   Something may have happened to the file while
    #   it's name was on the queue, notably a rename

    if not os.path.exists(path + filename):
        return

    if remove_boring:
        if not "test" in filename:
            found = set(yolo.yolo_file(path + filename))
            found_lifeforms = found & lifeforms
            if not found_lifeforms:
                os.system("sudo rm " + path + filename)
                return

    if debug:
        print("move", path + filename, " to ", website + filename)
    try:
        os.system("sudo cp -p " + path + filename + " " + website)
    except Exception as err:
        print("File copy failed:", err)


# expensive...


def build_website(website, title):
    """Call website builder"""
    debug = False

    try:
        command = (
            "sudo /usr/bin/imageindex " + website + " -reverse -title '" + title + "'"
        )
        if debug:
            print(command)
        os.system(command)
    except Exception as err:
        if debug:
            print("Failed to build website", err)


WEBSITETOOYOUNG = 10  # Minutes. Don't redo it this early
SHORTESTQUIETTIME = 10  # Don't rebuild unless it looks like a lull in comms


def generate_image_website(path, website, title):
    """Consume filenames from queue and transfer to website, regenerate at intervals"""
    website_birth = datetime.now()
    data_last_arrival = datetime.now()
    busy = psutil.cpu_percent(interval=None)

    debug = False

    expected_children = 1

    q = Queue()

    # Create instances of the Process class, one for each function

    p1 = Process(target=initiate_watch, args=(q, path))

    p1.start()

    signal.signal(signal.SIGTERM, handler)

    file_list = []
    new_data_written = False

    while True:
        try:
            item = q.get_nowait()
            #       If item wasn't available the above generated an Empty exception
            data_last_arrival = datetime.now()
            base, fname = os.path.split(item)

            if debug:
                print("File :", fname)
                print(" arrived in source directory:", base)

            try:
                parts = fname.split(".")
                extension = parts[1].lower()
                if extension != "jpg":
                    if debug:
                        print("File ignored\n")
                    continue

            except Exception as e:
                print(e)
                if debug:
                    print("File ignored\n")
                continue

            file_list.append(fname)

        except queue.Empty:
            if 0 < len(file_list):
                for i in range(len(file_list)):
                    transfer(path, file_list[i], website)
                file_list.clear()
                new_data_written = True
            else:
                sleep(30)

            #   Don't rebuild if system is busy . This captures the case where
            # lots of motion triggers are being rejected but no data ends up queued

            busy = psutil.cpu_percent(interval=None)
            if 50.0 < busy:
                continue

            # Don't rebuild if website too young or data arrived recently

            now = datetime.now()
            if new_data_written:
                if debug:
                    print("New file written: consider rebuilding website")
                if timedelta(minutes=WEBSITETOOYOUNG) < now - website_birth:
                    if timedelta(minutes=SHORTESTQUIETTIME) < now - data_last_arrival:
                        if debug:
                            print("Rebuild website")
                        build_website(website, title)
                        website_birth = datetime.now()
                        new_data_written = False
                    else:
                        if debug:
                            print("Recent data arrival supresses website rebuild")
                else:
                    if debug:
                        print("Too early to rebuild website")
            else:
                continue

        # Check child is (nominally) active

        child_count = 0
        for p in multiprocessing.active_children():
            child_count += 1
        if child_count < expected_children:
            print("Our child has gone missing")
            sys.exit()  # rely on systemd restart


if __name__ == "__main__":

    runfile = sys.argv.pop(0)
    inputargs = sys.argv
    if len(inputargs) != 3:
        print(
            "Incorrect usage! Should be : <path>/generate_website.py <File origin directory> <Website directory> <Website title>"
        )
        sys.exit()

    path = inputargs[0]
    website = inputargs[1]
    title = inputargs[2]

    if not os.path.exists(path):
        print("Input directory not found, sys.exiting")
        sys.exit()

    if not os.path.exists(website):
        print("Output website  directory not found, sys.exiting")
        sys.exit()

    print(
        "Form website on :",
        website,
        " from files on ",
        path,
        " for website called",
        title,
    )

    if remove_boring:
        yolo.initialise_yolo()

    generate_image_website(path, website, title)
