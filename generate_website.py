#
# Copy images from one directory as they appear in it
# Place them on a directory intended to host a website
# At carefully chosen intervals regenerate the index.html etc
# using imageindex to produce the index.html etc
# The latter operation is expensive iand we avoid doing it
# too frequently and when files are still moving


import signal, os
import multiprocessing
from multiprocessing import Queue
from multiprocessing import Pool
from multiprocessing import Process
from multiprocessing import active_children
from time import sleep
import inotify
import inotify.adapters

# Attempt orderly shutdown


def handler(signum, frame):
    signame = signal.Signals(signum).name
    print("Caught signal", signame)

    for p in multiprocessing.active_children():
        p.terminate()

    exit()




def act(q, path, filename):

    debug = False

    if debug:
        print(path + filename)
    q.put(path + filename)


def watch(q, i, path):

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if "IN_CLOSE_WRITE" in type_names:
            act(q, path, filename)


def initiate_watch(q, path):

    i = inotify.adapters.InotifyTree(path)
    watch(q, i, path)


import os
import queue

# Cheap...


def transfer(path, filename, website):

    debug = False

    if debug:
        print("move", path + filename, " to ", website + filename)
    try:
        response = os.system("sudo cp -p " + path + filename + " " + website)
    except Exception as err:
        print("File copy failed:", e)


# expensive...


def build_website(website, title):

    debug = False

    try:
        command = (
            "sudo /usr/bin/imageindex " + website + " -reverse -title '" + title + "'"
        )
        if debug:
            print(command)
        response = os.system(command)
    except Exception as err:
        if debug:
            print("Failed to build website", err)
        pass


from datetime import datetime, timedelta

websiteTooYoung = 10  # Minutes. Don't redo it this early
shortestQuietTime = 10  # Don't rebuild unless it looks like a lull in comms


def generate_image_website(path, website, title):

    website_birth = datetime.now()
    data_last_arrival = datetime.now()

    debug = False

    parent = multiprocessing.parent_process()
    parentPID = 0  # parent.pid

    expectedChildren = 1

    q = Queue()

    # Create instances of the Process class, one for each function

    p1 = Process(target=initiate_watch, args=(q, path))

    p1.start()

    signal.signal(signal.SIGTERM, handler)

    P1PID = p1.pid

    fileList = []

    new_data_written = False

    while True:

        try:
            item = q.get_nowait()
            #       If item wasn't available the above generated an Empty exception
            data_last_arrival = datetime.now()
            base, fname = os.path.split(item)

            try:
                parts = fname.split(".")
                extension = parts[1]
                if extension != "jpg":
                    continue
            except Exception as err:
                print(e)
                continue

            if debug:
                print("File :", fname)
                print(" arrived in source directory:", base)

            fileList.append(fname)

        except queue.Empty:

            if 0 < len(fileList):
                for i in range(len(fileList)):
                    transfer(path, fileList[i], website)
                fileList.clear()
                new_data_written = True
            else:
                sleep(30)

            # Don't rebuild if website too young or data arrived recently

            now = datetime.now()
            if new_data_written:
                if debug:
                    print("New file written: consider rebuilding website")
                if timedelta(minutes=websiteTooYoung) < now - website_birth:
                    if timedelta(minutes=shortestQuietTime) < now - data_last_arrival:
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

        childCount = 0
        for p in multiprocessing.active_children():
            childCount += 1
        if childCount < expectedChildren:
            print("Our child has gone missing")
            exit()  # rely on systemd restart


import sys

if __name__ == "__main__":

    runfile = sys.argv.pop(0)
    inputargs = sys.argv
    if len(inputargs) != 3:
        print(
            "Incorrect usage! Should be : <path>/generate_website.py <File origin directory> <Website directory> <Website title>"
        )
        exit()

    path = inputargs[0]
    website = inputargs[1]
    title = inputargs[2]

    print(
        "Form website on :",
        website,
        " from files on ",
        path,
        " for website called",
        title,
    )

    generate_image_website(path, website, title)
