#!/usr/bin/python3

import argparse
import configparser
import logging
import os
from datetime import datetime
from ridehail import animation as rhanimation, atom


class RideHailConfig():
    """
    Hold the configuration parameters for the simulation, which come from three
    places:
    - default values, unless overridden by
    - a configuration file, unless overridden by
    - command line arguments
    """

    # Some attributes have defaults
    city_size = 20
    vehicle_count = 1
    base_demand = 0.2
    trip_distribution = atom.TripDistribution.UNIFORM
    min_trip_distance = 0.0
    max_trip_distance = city_size
    time_blocks = 201
    smoothing_window = min(int(1.0 / base_demand), 1)
    results_window = int(time_blocks * 0.25)
    idle_vehicles_moving = True
    animation = False
    equilibration = False
    sequence = False
    equilibrate = "none"
    animate = "none"
    verbosity = 0
    log_file = None

    def __init__(self, use_config_file=True):
        """
        Read the configuration file  to set up the parameters
        """
        if use_config_file:
            parser = self._parser()
            args, extra = parser.parse_known_args()
            config_file = self._set_config_file(args)
            self.start_time = f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
            self.config_file_dir = os.path.dirname(config_file)
            self.config_file_root = (os.path.splitext(
                os.path.split(config_file)[1])[0])
            self.jsonl_file = ((f"./output/{self.config_file_root}"
                                f"-{self.start_time}.jsonl"))
            self._set_options_from_config_file(config_file)
            self._override_options_from_command_line(args)
            self._fix_option_enums()
        if self.verbosity == 0:
            loglevel = 30  # logging.WARNING  # 30
        elif self.verbosity == 1:
            loglevel = 20  # logging.INFO  # 20
        elif self.verbosity == 2:
            loglevel = 10  # logging.DEBUG  # 10
        else:
            loglevel = 20  # logging.INFO  # 20
        if self.log_file:
            logging.basicConfig(
                filename=self.log_file,
                filemode="w",
                level=loglevel,
                format="%(asctime)-15s %(levelname)-8s%(message)s")
            logging.info(f"Logging to file {self.log_file}")
        else:
            logging.basicConfig(
                level=loglevel,
                format="%(asctime)-15s %(levelname)-8s%(message)s")
            logging.info(f"Log level set to {loglevel}")
        self._log_config()

    def _log_config(self):
        for attr in dir(self):
            attr_name = attr.__str__()
            if not attr_name.startswith("_"):
                logging.info(f"config.{attr_name} = {getattr(self, attr)}")

    def _set_config_file(self, args):
        """
        Set self.config_file
        """
        if args.config_file is not None:
            config_file = args.config_file
        else:
            # The default config file is username.config
            # look for username.config on both Windows (USERNAME)
            # and Linux (USER)
            if os.name == "nt":
                username = os.environ['USERNAME']
            else:
                username = os.environ['USER']
            config_file = username + ".config"
        if not os.path.isfile(config_file):
            print(f"Configuration file {config_file} not found.")
            exit(False)
        return config_file

    def _set_options_from_config_file(self, config_file, included=False):
        """
        Read a configuration file
        """
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        if included is False:
            if "include_file" in config["DEFAULT"].keys():
                # only one level of inclusion
                include_config_file = config['DEFAULT']['include_file']
                include_config_file = os.path.join(self.config_file_dir,
                                                   include_config_file)
                self._set_options_from_config_file(include_config_file,
                                                   included=True)
            if (config.has_section("ANIMATION")
                    and "include_file" in config["ANIMATION"].keys()):
                # only one level of inclusion
                include_config_file = config['ANIMATION']['include_file']
                include_config_file = os.path.join(self.config_file_dir,
                                                   include_config_file)
                self._set_options_from_config_file(include_config_file,
                                                   included=True)
        if config:
            self._set_default_section_options(config)
        if config.has_section("ANIMATION"):
            self._set_animation_section_options(config)
        if config.has_section("EQUILIBRATION"):
            self._set_equilibration_section_options(config)
        if config.has_section("SEQUENCE"):
            self._set_sequence_section_options(config)
        if config.has_section("IMPULSES"):
            self._set_impulses_section_options(config)

    def _set_default_section_options(self, config):
        default = config["DEFAULT"]
        if config.has_option("DEFAULT", "city_size"):
            self.city_size = default.getint("city_size")
        if config.has_option("DEFAULT", "vehicle_count"):
            self.vehicle_count = default.getint("vehicle_count")
        if config.has_option("DEFAULT", "base_demand"):
            self.base_demand = default.getfloat("base_demand")
        if config.has_option("DEFAULT", "trip_distribution"):
            self.trip_distribution = default.get("trip_distribution")
        if config.has_option("DEFAULT", "min_trip_distance"):
            self.min_trip_distance = default.getint("min_trip_distance")
        if config.has_option("DEFAULT", "max_trip_distance"):
            self.max_trip_distance = default.getint("max_trip_distance")
        else:
            self.max_trip_distance = self.city_size
        if config.has_option("DEFAULT", "time_blocks"):
            self.time_blocks = default.getint("time_blocks")
        if config.has_option("DEFAULT", "log_file"):
            self.log_file = default["log_file"]
        if config.has_option("DEFAULT", "verbosity"):
            self.verbosity = default.getint("verbosity", fallback=0)
        if config.has_option("DEFAULT", "animation"):
            self.animation = default.getboolean("animation", fallback=False)
        if config.has_option("DEFAULT", "equilibration"):
            self.equilibration = default.getboolean("equilibration",
                                                    fallback=False)
        if config.has_option("DEFAULT", "sequence"):
            self.sequence = default.getboolean("sequence", fallback=False)
        if config.has_option("DEFAULT", "results_window"):
            self.results_window = default.getint("results_window")
        if config.has_option("DEFAULT", "idle_vehicles_moving"):
            self.idle_vehicles_moving = default.getboolean(
                "idle_vehicles_moving")

    def _set_animation_section_options(self, config):
        """
        """
        animation = config["ANIMATION"]
        if config.has_option("ANIMATION", "animate"):
            self.animate = animation.get("animate")
        if config.has_option("ANIMATION", "animate_update_period"):
            self.animate_update_period = (
                animation.getint("animate_update_period"))
        if config.has_option("ANIMATION", "interpolate"):
            self.interpolate = animation.getint("interpolate")
        if config.has_option("ANIMATION", "animation_output"):
            self.animation_output = animation.get("animation_output")
        if config.has_option("ANIMATION", "imagemagick_dir"):
            self.imagemagick_dir = animation.get("imagemagick_dir")
        if config.has_option("ANIMATION", "smoothing_window"):
            self.smoothing_window = animation.getint("smoothing_window")

    def _set_equilibration_section_options(self, config):
        equilibration = config["EQUILIBRATION"]
        if config.has_option("EQUILIBRATION", "equilibrate"):
            self.equilibrate = equilibration.get("equilibrate")
        if config.has_option("EQUILIBRATION", "price"):
            self.price = equilibration.getfloat("price", fallback=1.0)
        if config.has_option("EQUILIBRATION", "platform_commission"):
            self.platform_commission = (equilibration.getfloat(
                "platform_commission", fallback=0))
        if config.has_option("EQUILIBRATION", "reserved_wage"):
            self.reserved_wage = equilibration.getfloat("reserved_wage",
                                                        fallback=0.5)
        if config.has_option("EQUILIBRATION", "demand_elasticity"):
            self.demand_elasticity = equilibration.getfloat(
                "demand_elasticity", fallback=0.5)
        if config.has_option("EQUILIBRATION", "equilibration_interval"):
            self.equilibration_interval = equilibration.getint(
                "equilibration_interval", fallback=5)

    def _set_sequence_section_options(self, config):
        sequence = config["SEQUENCE"]
        if config.has_option("SEQUENCE", "price_repeat"):
            self.price_repeat = sequence.getint("price_repeat", fallback=1)
        if config.has_option("SEQUENCE", "price_increment"):
            self.price_increment = sequence.getfloat("price_increment",
                                                     fallback=0.1)
        if config.has_option("SEQUENCE", "price_max"):
            self.price_max = sequence.getfloat("price_max", fallback=2)
        if config.has_option("SEQUENCE", "vehicle_count_increment"):
            self.vehicle_count_increment = sequence.getint(
                "vehicle_count_increment", fallback=1)
        if config.has_option("SEQUENCE", "vehicle_count_max"):
            self.vehicle_count_max = sequence.getint("vehicle_count_max",
                                                     fallback=10)
        if config.has_option("SEQUENCE", "vehicle_cost_max"):
            self.vehicle_cost_max = sequence.getfloat("vehicle_cost_max",
                                                      fallback=0.8)
        if config.has_option("SEQUENCE", "vehicle_cost_increment"):
            self.vehicle_cost_increment = sequence.getfloat(
                "vehicle_cost_increment", fallback=0.1)

    def _set_impulses_section_options(self, config):
        impulses = config["IMPULSES"]
        if config.has_option("IMPULSES", "impulse_list"):
            self.impulse_list = impulses.get("impulse_list")
            self.impulse_list = eval(self.impulse_list)

    def _override_options_from_command_line(self, args):
        """
        Override configuration options with command line settings
        """
        args_dict = vars(args)
        for key, val in args_dict.items():
            if hasattr(self, key) and key != "config_file" and val is not None:
                setattr(self, key, val)

    def _fix_option_enums(self):
        """
        For options that have validation constraints, impose them
        For options that are supposed to be enum values, fix them
        """
        if self.equilibration:
            for eq_option in list(atom.Equilibration):
                if self.equilibrate.lower()[0] == eq_option.name.lower()[0]:
                    self.equilibrate = eq_option
                    break
            if self.equilibrate not in list(atom.Equilibration):
                print(f"equilibration must start with s, d, f, or n")
        else:
            self.equilibrate = atom.Equilibration.NONE
        if self.animation:
            for animate_option in list(rhanimation.Animation):
                if self.animate.lower()[0] == animate_option.value.lower()[0]:
                    self.animate = animate_option
                    break
            if self.animate not in list(rhanimation.Animation):
                print(f"animate must start with m, s, a, or n")
            if (self.animate not in (rhanimation.Animation.MAP,
                                     rhanimation.Animation.ALL)):
                # Interpolation is relevant only if the map is displayed
                self.interpolate = 1
        else:
            self.animate = rhanimation.Animation.NONE
        if self.trip_distribution.lower().startswith("b"):
            if self.trip_distribution == "beta_short":
                self.trip_distribution = atom.TripDistribution.BETA_SHORT
            else:
                self.trip_distribution = atom.TripDistribution.BETA_LONG
        else:
            self.trip_distribution = atom.TripDistribution.UNIFORM
        city_size = 2 * int(self.city_size / 2)
        if city_size != self.city_size:
            print(f"City size must be an even integer"
                  f": reset to {city_size}")
            self.city_size = city_size

    def _parser(self):
        """
        Define, read and parse command-line arguments.
        Defaults should all be None to avoid overwriting config file
        entries
        """
        parser = argparse.ArgumentParser(
            description="Simulate ride-hail vehicles and trips.",
            usage="%(prog)s [options]",
            fromfile_prefix_chars='@')
        parser.add_argument("config_file",
                            metavar="config_file",
                            nargs="?",
                            action="store",
                            type=str,
                            default=None,
                            help="""Configuration file""")
        parser.add_argument(
            "-a",
            "--animate",
            metavar="animate",
            action="store",
            type=str,
            default=None,
            help="""animate 'all', 'stats', 'bar', 'map', 'none',
                        ['map']""")
        parser.add_argument(
            "-ivm",
            "--idle_vehicles_moving",
            metavar="idle_vehicles_moving",
            action="store",
            type=bool,
            default=None,
            help="""True if vehicles should drive around looking for
                        a ride; False otherwise.""")
        parser.add_argument(
            "-bd",
            "--base_demand",
            metavar="base_demand",
            action="store",
            type=float,
            default=None,
            help="Base demand (request rate) before price takes effect")
        parser.add_argument("-cs",
                            "--city_size",
                            metavar="city_size",
                            action="store",
                            type=int,
                            default=None,
                            help="""Length of the city grid, in blocks.""")
        parser.add_argument("-vs",
                            "--vehicle_count",
                            metavar="vehicle_count",
                            action="store",
                            type=int,
                            default=None,
                            help="number of vehicles")
        parser.add_argument("-au",
                            "--animate_update_period",
                            metavar="animate_update_period",
                            action="store",
                            type=int,
                            default=None,
                            help="How often to update charts")
        parser.add_argument("-ei",
                            "--equilibration_interval",
                            metavar="equilibration_interval",
                            type=int,
                            default=None,
                            action="store",
                            help="""Interval at which to adjust supply and/or
                        demand""")
        parser.add_argument(
            "-eq",
            "--equilibration",
            metavar="equilibration",
            type=str,
            default=None,
            action="store",
            help="""Adjust vehicle count and ride requests to equilibrate""")
        parser.add_argument("-rw",
                            "--reserved_wage",
                            metavar="reserved_wage",
                            action="store",
                            type=float,
                            default=None,
                            help="""Vehicle cost per unit time""")
        parser.add_argument(
            "-i",
            "--interpolate",
            metavar="interpolate",
            action="store",
            type=int,
            default=None,
            help="""Number of interpolation points when updating
                        the map display""")
        parser.add_argument("-img",
                            "--imagemagick_dir",
                            metavar="imagemagick_dir",
                            action="store",
                            type=str,
                            default=None,
                            help="""ImageMagick Directory""")
        parser.add_argument("-l",
                            "--log_file",
                            metavar="log_file",
                            action="store",
                            type=str,
                            default=None,
                            help=("Logfile name. By default, log messages "
                                  "are written to the screen only"))
        parser.add_argument(
            "-ao",
            "--animation_output",
            metavar="animation_output",
            action="store",
            type=str,
            default=None,
            help="""filename: graphics output as a file; gif or mp4""")
        parser.add_argument("-p",
                            "--price",
                            action="store",
                            type=float,
                            default=None,
                            help="Fixed price")
        parser.add_argument("-t",
                            "--time_blocks",
                            metavar="time_blocks",
                            action="store",
                            type=int,
                            default=None,
                            help="number of time blocks")
        parser.add_argument(
            "-v",
            "--verbosity",
            action="store",
            type=int,
            default=0,
            help="""log verbosity level: 0=WARNING, 1=INFO, 2=DEBUG""")
        parser.add_argument("-sw",
                            "--smoothing_window",
                            metavar="smoothing_window",
                            action="store",
                            type=int,
                            default=None,
                            help="""Smoothing window for computing averages""")
        return parser
