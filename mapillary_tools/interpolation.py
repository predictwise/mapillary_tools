import processing
import uploader
import os
import sys
from geo import interpolate_lat_lon
from exif_write import ExifEdit
from exif_read import ExifRead

import process_csv
import csv


def format_datetime(timestamps_interpolated, time_utc=False, time_format="%Y-%m-%dT%H:%M:%SZ"):

    if time_utc:
        try:
            timestamps_formated = [int((datetime_timestamp - EPOCH).total_seconds()
                                       * 1000.0) for datetime_timestamp in timestamps_interpolated]
        except:
            print("Formating timestamps from datetime to UTC failed...")
            sys.exit()
    else:
        try:
            timestamps_formated = [datetime_timestamp.strftime(
                time_format) for datetime_timestamp in timestamps_interpolated]
        except:
            print("Formating timestamps from datetime to time format {} failed...".format(
                time_format))
            sys.exit()
    return timestamps_formated


def interpolation(data,
                  file_in_path=None,
                  file_format="csv",
                  time_column=0,
                  delimiter=",",
                  time_utc=False,
                  time_format="%Y-%m-%dT%H:%M:%SZ",
                  header=False,
                  keep_original=False,
                  import_path=None,
                  max_time_delta=1,
                  verbose=False):

    if not data:
        print("Error, you must specify the data for interpolation.")
        print('Choose between "missing_gps" or "identical_timestamps"')
        sys.exit()

    if not import_path and not file_in_path:
        print("Error, you must specify a path to data, either path to directory with images or path to an external log file.")
        sys.exit()

    if file_in_path:
        if not os.path.isfile(file_in_path):
            print("Error, specified input file does not exist, exiting...")
            sys.exit()
        if file_format != "csv":
            print("Only csv file format is supported at the moment, exiting...")
            sys.exit()

        csv_data = process_csv.read_csv(
            file_in_path, delimiter=delimiter, header=header)

        if data == "identical_timestamps":
            timestamps = csv_data[time_column]
            timestamps_datetime = [process_csv.format_time(
                timestamp, time_utc, time_format) for timestamp in timestamps]

            timestamps_interpolated = processing.interpolate_timestamp(
                timestamps_datetime)

            csv_data[time_column] = format_datetime(
                timestamps_interpolated, time_utc, time_format)

            file_out = file_in_path if not keep_original else file_in_path[
                :-4] + "_processed." + file_format

            with open(file_out, "w") as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=delimiter)
                for row in zip(*csv_data):
                    csvwriter.writerow(row)
            sys.exit()
        elif data == "missing_gps":
            print(
                "Error, missing gps interpolation in an external log file not supported yet, exiting...")
            sys.exit()
        else:
            print("Error unsupported data for interpolation, exiting...")
            sys.exit()

    if import_path:
        if not os.path.isdir(import_path):
            print("Error, specified import path does not exist, exiting...")
            sys.exit()

        # get list of files to process
        process_file_list = uploader.get_total_file_list(import_path)
        if not len(process_file_list):
            print("No images found in the import path " + import_path)
            sys.exit()

        if data == "missing_gps":
            # get geotags from images and a list of tuples with images missing geotags
            # and their timestamp
            geotags, missing_geotags = processing.get_images_geotags(
                process_file_list)
            if not len(missing_geotags):
                print("No images in directory {} missing geotags, exiting...".format(
                    import_path))
                sys.exit()
            if not len(geotags):
                print("No images in directory {} with geotags.".format(import_path))
                sys.exit()

            sys.stdout.write("Interpolating gps for {} images missing geotags.".format(
                len(missing_geotags)))

            counter = 0
            for image, timestamp in missing_geotags:
                counter += 1
                sys.stdout.write('.')
                if (counter % 100) == 0:
                    print("")
                # interpolate
                try:
                    lat, lon, bearing, elevation = interpolate_lat_lon(
                        geotags, timestamp, max_time_delta)
                except Exception as e:
                    print("Error, {}, interpolation of latitude and longitude failed for image {}".format(
                        e, image))
                    continue
                # insert into exif
                exif_edit = ExifEdit(image)
                if lat and lon:
                    exif_edit.add_lat_lon(lat, lon)
                else:
                    print(
                        "Error, lat and lon not interpolated for image {}.".format(image))
                if bearing:
                    exif_edit.add_direction(bearing)
                else:
                    if verbose:
                        print(
                            "Warning, bearing not interpolated for image {}.".format(image))
                if elevation:
                    exif_edit.add_altitude(elevation)
                else:
                    if verbose:
                        print(
                            "Warning, altitude not interpolated for image {}.".format(image))

                file_out = image if not keep_original else image[
                    :-4] + "_processed."
                exif_edit.write(filename=file_out)

        elif data == "identical_timestamps":

            sys.stdout.write("Loading image timestamps.")

            # read timestamps
            timestamps = []
            counter = 0
            for image in process_file_list:

                # print progress
                counter += 1
                sys.stdout.write('.')
                if (counter % 100) == 0:
                    print("")

                # load exif
                exif = ExifRead(image)
                timestamp = exif.extract_capture_time()
                if timestamp:
                    timestamps.append(timestamp)
                else:
                    print("Capture could not be extracted for image {}.".format(image))

            # interpolate
            timestamps_interpolated = processing.interpolate_timestamp(
                timestamps)

            print("")
            sys.stdout.write("Interpolating identical timestamps.")
            counter = 0

            # write back
            for image, timestamp in zip(process_file_list, timestamps_interpolated):

                # print progress
                counter += 1
                sys.stdout.write('.')
                if (counter % 100) == 0:
                    print("")

                # load exif
                exif_edit = ExifEdit(image)
                exif_edit.add_date_time_original(timestamp)

                # write to exif
                file_out = image if not keep_original else image[
                    :-4] + "_processed."
                exif_edit.write(filename=file_out)

            sys.exit()
        else:
            print("Error unsupported data for interpolation, exiting...")
            sys.exit()
    print("")
