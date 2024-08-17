import time
import os
import timestamptotime
import glob


def make_date_match_name(file_location, file_name, file_extension):
    ''' If you don't do this, the image order gets mangled, sometine severely  '''
    full_filename = file_location + file_name + file_extension

    name_datetime = timestamptotime.txtTimestampToTime(file_name)

    # Get the current time
    current_time = name_datetime[1].timestamp()

    # Set the desired creation and modification datetime
    creation_time = current_time
    modification_time = current_time

    # Set the creation and modification datetime of the file
    full_name = file_location + "/" + file_name + file_extension
    print(full_name)
    os.utime(
        full_name,
        (creation_time, modification_time),
    )


def change_dates(these):

    imgnames = sorted(glob.glob(these))

    for image in imgnames:
        file_tuple = os.path.splitext(image)
        file_extension = file_tuple[1]
        file = file_tuple[0]
        file_name = os.path.basename(file)
        path = os.path.dirname(file)

        make_date_match_name(path, file_name, file_extension)


if __name__ == "__main__":

    these = "/exdrive/Snapshots/Local/2*.jpg"
    change_dates(these)
    these = "/var/www/html/2*.jpg"
    change_dates(these)


