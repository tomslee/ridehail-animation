#!/usr/bin/python3

import configparser
import logging
import os
from ridehail.plot import Draw
from ridehail.simulation import Equilibration

logger = logging.getLogger(__name__)


class Config():
    """
    Hold the configuration parameters for the simulation, which come from three
    places:
    - default values, unless overridden by
    - a configuration file, unless overridden by
    - command line arguments
    """
    def __init__(self, args=None):
        """
        Read the configuration file  to set up the parameters
        """
        self.config_file = None
        self.log_level = logging.INFO
        if args is not None:
            self.config_file = args.config_file
            try:
                if args.verbose:
                    self.log_level = logging.DEBUG
                else:
                    self.log_level = logging.INFO
            except Exception:
                self.log_level = logging.INFO
        config = configparser.ConfigParser()
        if self.config_file is None:
            # The default config file is username.config
            # look for username.config on both Windows (USERNAME)
            # and Linux (USER)
            if os.name == "nt":
                username = os.environ['USERNAME']
            else:
                username = os.environ['USER']
            self.config_file = username + ".config"
            logger.info(f"Reading configuration file {self.config_file}")
            if not os.path.isfile(self.config_file):
                logger.error(
                    f"Configuration file {self.config_file} not found.")
        config.read(self.config_file)

        # Fill in individual configuration values
        # City size
        self.city_size = int(args.city_size if args.
                             city_size else config["DEFAULT"]["city_size"])
        logger.info(f"City size = {self.city_size}")
        # Driver count
        self.driver_count = int(args.driver_count if args.driver_count else
                                config["DEFAULT"]["driver_count"])
        logger.info(f"Driver counts = {self.driver_count}")
        # Request rate
        self.request_rate = float(args.request_rate if args.request_rate else
                                  config["DEFAULT"]["request_rate"])
        logger.info(f"Request rate = {self.request_rate}")
        # Time periods
        self.time_periods = int(args.time_periods if args.time_periods else
                                config["DEFAULT"]["time_periods"])
        logger.info(f"Time periods = {self.time_periods}")
        # Log file TODO not sure if this works
        self.log_file = str(
            args.log_file if args.log_file else config["DEFAULT"]["log_file"])
        logger.info(f"Log file = {self.log_file}")
        # Verbose output
        self.verbose = bool(
            args.verbose if args.verbose else config["DEFAULT"]["verbose"])
        logger.info(f"Verbose = {self.verbose}")
        # Quiet output
        self.quiet = bool(
            args.quiet if args.quiet else config["DEFAULT"]["quiet"])
        logger.info(f"Quiet = {self.quiet}")
        # Draw maps or charts
        self.draw = str(args.draw if args.draw else config["DEFAULT"]["draw"])
        for draw_option in list(Draw):
            if self.draw == draw_option.value:
                self.draw = draw_option
                break
        logger.info(f"Draw = {self.draw}")
        # Draw update period
        self.draw_update_period = int(
            args.draw_update_period if args.
            draw_update_period else config["DEFAULT"]["draw_update_period"])
        logger.info(f"Draw update period = {self.draw_update_period}")
        # Interpolation points
        self.interpolate = int(args.interpolate if args.interpolate else
                               config["DEFAULT"]["interpolate"])
        logger.info(f"Interpolation points = {self.interpolate}")
        # Equilibrate
        self.equilibrate = str(args.equilibrate if args.equilibrate else
                               config["DEFAULT"]["equilibrate"])
        logger.info(f"Equilibration = {self.equilibrate}")
        # Rolling window
        self.rolling_window = int(args.rolling_window if args.rolling_window
                                  else config["DEFAULT"]["rolling_window"])
        logger.info(f"Rolling window = {self.rolling_window}")
        # Output file for charts
        self.output = str(
            args.output if args.output else config["DEFAULT"]["output"])
        logger.info(f"Output file for charts = {self.output}")
        # ImageMagick directory
        self.imagemagick_dir = str(args.imagemagick_dir if args.imagemagick_dir
                                   else config["DEFAULT"]["imagemagick_dir"])
        logger.info(f"ImageMagick_Dir = {self.imagemagick_dir}")
        # Available drivers moving
        self.available_drivers_moving = bool(
            args.available_drivers_moving if args.available_drivers_moving else
            config["DEFAULT"]["available_drivers_moving"])
        logger.info(
            f"Available drivers moving = {self.available_drivers_moving}")
        if self.equilibrate and config.has_section("EQUILIBRATION"):
            for option in list(Equilibration):
                if self.equilibrate.lower()[0] == option.name.lower()[0]:
                    self.equilibrate = option
                    logger.info(f"Equilibration method is {option.name}")
                    break
            if self.equilibrate not in list(Equilibration):
                logger.error(f"equilibrate must start with s, d, f, or n")
            # Price
            self.price = float(
                args.price if args.price else config["EQUILIBRATION"]["price"])
            logger.info(f"Price = {self.price}")
            # Driver cost
            self.driver_cost = float(args.driver_cost if args.driver_cost else
                                     config["EQUILIBRATION"]["driver_cost"])
            logger.info(f"Driver cost = {self.driver_cost}")
            # Ride utility
            self.ride_utility = float(
                args.ride_utility if args.
                ride_utility else config["EQUILIBRATION"]["ride_utility"])
            logger.info(f"Ride utility = {self.ride_utility}")
            # Wait cost
            self.wait_cost = float(args.wait_cost if args.wait_cost else
                                   config["EQUILIBRATION"]["wait_cost"])
            logger.info(f"Wait cost = {self.wait_cost}")
            # Equilibration interval
            self.equilibration_interval = int(
                args.equilibration_interval if args.equilibration_interval else
                config["EQUILIBRATION"]["equilibration_interval"])
            logger.info(
                f"Equilibration interval = {self.equilibration_interval}")
        if config.has_section("SEQUENCE"):
            if config.has_option("SEQUENCE", "run_sequence"):
                self.run_sequence = str(config["SEQUENCE"]["run_sequence"])
                if (self.run_sequence.lower().startswith("f")
                        or self.run_sequence.startswith("0")):
                    self.run_sequence = False
            else:
                self.run_sequence = False
            logger.info(f"Run sequence = {self.run_sequence}")
            if config.has_option("SEQUENCE", "request_rate_repeat"):
                self.request_rate_repeat = int(
                    config["SEQUENCE"]["request_rate_repeat"])
            else:
                self.request_rate_repeat = 1
            if config.has_option("SEQUENCE", "request_rate_increment"):
                self.request_rate_increment = float(
                    config["SEQUENCE"]["request_rate_increment"])
            else:
                self.request_rate_increment = 1.0
            if config.has_option("SEQUENCE", "request_rate_max"):
                self.request_rate_max = float(
                    config["SEQUENCE"]["request_rate_max"])
            else:
                self.request_rate_max = 1.0
            if config.has_option("SEQUENCE", "driver_count_increment"):
                self.driver_count_increment = int(
                    config["SEQUENCE"]["driver_count_increment"])
            else:
                self.driver_count_increment = 1
            if config.has_option("SEQUENCE", "driver_count_max"):
                self.driver_count_max = int(
                    config["SEQUENCE"]["driver_count_max"])
            else:
                self.driver_count_max = 1