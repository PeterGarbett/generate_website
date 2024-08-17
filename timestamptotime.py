import os
import shutil
import glob
import datetime

dryRun = False


def txtTimestampToTime(filename):

    debug = False

    # Convert something of the form
    # 2024_03_06_14_24_21_423461_l<junk>.<junk>
    # to datetime object

    try:
        timestamp = filename.replace("_", "-", 2)
        timestamp = timestamp.replace("_", " ", 1)
        timestamp = timestamp.replace("_", ":", 2)
        timestamp = timestamp.replace("_", ".", 1)
        timestamp = timestamp.split("_l")
        timestamp = timestamp[0]

        # the fact that strptime isn't capable of coping
        # directly with the output of datetime now is
        # really poor.

        stampNoMs = timestamp[:-7]
        MicrosecondsTXT = timestamp.split(".")[1]
        MicrosecondsTXT = MicrosecondsTXT.split("_")[0]
        MicrosecondsTXT = MicrosecondsTXT.strip()
        if debug:
            print(filename, "microseconds:", MicrosecondsTXT)
    except Exception as e:
        print(filename, "Error extracting timestamp ", e)
        when = datetime.datetime.now()  # default to new
        return (filename, when)

    try:
        if debug:
            print("convert:", MicrosecondsTXT)
        Microseconds = int(MicrosecondsTXT)
        if debug:
            print("converted:", Microseconds)

        # Remove the extra junk digits we have in some cases

        stampNoMs = stampNoMs.split(".")[0]
        when = datetime.datetime.strptime(stampNoMs, "%Y-%m-%d %H:%M:%S")
        when = when.replace(microsecond=Microseconds)
    except Exception as e:
        print(filename, "Error extracting microsecond timestamp ", e)
        when = datetime.datetime.now()  # default to new

    return (filename, when)

