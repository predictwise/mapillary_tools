
from mapillary_tools import process_video
from mapillary_tools.process_geotag_properties import process_geotag_properties


class Command:
    name = 'extract_geotag_data'
    help = "Process unit tool : Extract and process time and location properties."

    def add_basic_arguments(self, parser):
        parser.add_argument(
            '--rerun', help='rerun the processing', action='store_true', required=False)
        parser.add_argument(
            '--skip_subfolders', help='Skip all subfolders and import only the images in the given directory path.', action='store_true', default=False, required=False)

    def add_advanced_arguments(self, parser):
        parser.add_argument('--geotag_source', help='Provide the source of date/time and gps information needed for geotagging.', action='store',
                            choices=['exif', 'gpx', 'gopro_video', 'nmea'], default="exif", required=False)
        parser.add_argument(
            '--geotag_source_path', help='Provide the path to the file source of date/time and gps information needed for geotagging.', action='store',
            default=None, required=False)
        parser.add_argument(
            '--local_time', help='Assume image timestamps are in your local time', action='store_true', default=False, required=False)
        parser.add_argument('--sub_second_interval',
                            help='Sub second time between shots. Used to set image times with sub-second precision',
                            type=float, default=0.0, required=False)
        parser.add_argument('--offset_time', default=0., type=float,
                            help='time offset between the camera and the gps device, in seconds.', required=False)
        parser.add_argument('--offset_angle', default=0., type=float,
                            help='offset camera angle (90 for right facing, 180 for rear facing, -90 for left facing)', required=False)
        parser.add_argument("--use_gps_start_time",
                            help="Use GPS trace starting time in case of derivating timestamp from filename.", action="store_true", default=False, required=False)

    def run(self, args):
        if args.geotag_source == 'blackvue_videos' and not args.device_make:
            args.device_make = "Blackvue"
        process_geotag_properties(**vars(args))
