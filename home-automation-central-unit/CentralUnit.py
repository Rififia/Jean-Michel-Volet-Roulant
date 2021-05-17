import time
import argparseNoExit
import traceback

from re import match
from importlib import import_module
from ArduinoSerial import ArduinoSerial
from CentralUnitCommunicator import CentralUnitCommunicator


class CentralUnit:
    """
    CentralUnit for the Super Volet Roland's project. Will take all the
    decisions and tells the Arduino what to do with the shutters, according
    to (in order) the user's will, the time, and the environment.
    """
    USER_MODE_AUTO = 1
    USER_MODE_OPEN = 2
    USER_MODE_CLOSE = 3

    SHUTTERS_OPENED = 4
    SHUTTERS_CLOSED = 5

    PLAIN_DAY = 6
    PLAIN_NIGHT = 7

    ARDUINO_OPEN_SHUTTERS = 8
    ARDUINO_CLOSE_SHUTTERS = 16
    ARDUINO_GET_ENV = 32

    def __init__(self, /, *, initialisation_command: str,
                 communicator_suffix: str = "File",
                 communicator_args=None,
                 arduino_serial_args=None):
        """
        Entry point for CentralUnit. Initialises attributes but does not run
        self.loop().
        :param initialisation_command: This command is ran immediately after
        the initialisation. This is useful for example to configure the CU
        using set_settings command.
        :param communicator_suffix: The suffix to create communicator's
        class name (will be appended to CentralUnitCommunicator).
        :type: str
        :param communicator_args: Kwargs for the communicator.
        :param arduino_serial_args: Kwargs for ArduinoSerial.
        :rtype: None
        """
        if not match('[A-Z0-9][a-z0-9]*', communicator_suffix):
            raise ValueError("Invalid suffix for central unit's communicator"
                             "class")

        if communicator_args is None:
            communicator_args = {}

        if arduino_serial_args is None:
            arduino_serial_args = {
                'port': 'COM1',
                'baudrate': 9600,
                'timeout': 1
            }

        # After communicator's initialisation, we can put in place a decent
        # logging.
        self._init_communicator(communicator_suffix, communicator_args)

        try:
            self._init_attributes()
            self._init_arduino(**arduino_serial_args)
            self.parse_command(initialisation_command)
        except Exception as e:
            self._proper_exit(1, e)

    def _init_arduino(self, port: str, baudrate: int, timeout: int):
        """
        Initialises ArduinoSerial object to communicate with the Arduino.
        :param port: The port used to connect to the Arduino
        :type: str
        :param baudrate: The baudrate for the connection.
        :type: int
        :param timeout: The timeout.
        :type: int
        :return:
        :rtype: None
        """
        self.arduino = ArduinoSerial(
            # Arduino should be adapted to ArduinoSerial's specification
            programmed_for_as=True,
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            log_fn=lambda msg: self._Communicator.log(
                msg, "arduino-serial", "status"
            )
        )

    def _init_attributes(self):
        """
        Initialises CentralUnit's attributes.
        :return:
        :rtype: None
        """
        # When set to False, the program will terminate properly
        self.__loop = True

        # Sometimes we want to keep the shutters closed for a defined time 
        # even if the conditions justify to open them. This avoids having the
        # shutters keep opening and closing all the time.
        self.__last_closed = 0

        # Keeps track of the current shutters' state (so it doesn't bother 
        # asking the Arduino to do something it already did)
        self.__shutters_state = self.SHUTTERS_OPENED

        # Argparser will help us parse commands the CU will receive.
        self.__argparser = argparseNoExit.ArgumentParserNoExit(
            add_help=False,
            exit_on_error=False
        )
        # We need to define the available commands and their parameters.
        self._init_commands()

        # The CU is configurable. Here is the default configuration. See 
        # self._init_commands with the definition of arguments for command
        # set_settings to see allowed values.
        self.__config = {
            # The mode currently running. The user can switch between
            # arbitrary closed or opened shutters, or automatic shutters mode.
            "user_mode": self.USER_MODE_AUTO,

            # When SHUTTERS_STATE is USER_MODE_AUTO, the CU checks for time,
            # temperature and luminosity each <this configuration variable>
            # seconds.
            "time_check": 600,

            # Defines during which hour of the day the sun rises, in 24h mode.
            # Precision: putting it at 7 means the program will consider
            # that it's sunrise between 7:00 included and 8:00 non included.
            "sunrise_hour": 7,

            # Defines during which hour of the day the sun sets.
            "sunset_hour": 19,

            # Defines the limit in lux under which the program considers the
            # sky has
            # a low luminosity (dark sky)
            # < 100lux is a dark sky (bad weather or late sunset / early
            # sunrise) according to
            # https://en.wikipedia.org/wiki/Lux#Illuminance -Wikipedia's
            # authors, CC-BY-SA-4.0
            "low_light_threshold": 100,

            # Defines the limit in Celsius under which it is considered very
            # cold outside.
            "low_temp_threshold": 0,

            # Defines the limit in Celsius above which it is considered
            # very hot outside.
            "high_temp_threshold": 30,

            # Whether the central unit will deal with environment conditions
            # and close the shutters in plain day if needed.
            "adapt_with_env_in_plain_day": True
        }

        # This variable keeps track of the last time it updated the
        # shutters, for automatic shutters mode.
        self.__last_check = time.time() - self.__config["time_check"]

    def _init_commands(self):
        """
        Initialises ArgumentParser instances, with one subparser per
        command. It makes things easier to generate error messages while
        parsing commands.
        :return:
        :rtype: None
        """
        sub_argparse = self.__argparser.add_subparsers(dest="command")
        subparsers = {
            "set_settings": sub_argparse.add_parser('set_settings',
                                                    add_help=None),
            "log_setting": sub_argparse.add_parser('get_setting',
                                                   add_help=None),
            "force_update": sub_argparse.add_parser('force_update',
                                                    add_help=None),
            "shutdown": sub_argparse.add_parser('shutdown', add_help=None)
        }

        # Functions to filter arguments with argparse
        def valid_time(in_val: str):
            """
            Checks if the value is a valid time in seconds, an int >= 0
            :param in_val:
            :type: str
            :raises: ValueError
            :rtype: int
            """
            val = int(in_val)
            if val < 0:
                raise ValueError("a valid_time should be an int >= 0")
            return val

        def lux(in_val: str):
            """
            Checks if the value is a lux value, an int >= 0.
            :param in_val:
            :type: str
            :raises: ValueError
            :rtype: int
            """
            val = int(in_val)
            if val < 0:
                raise ValueError("lux should be an int >= 0")
            return val

        def low_tmp36_temp(in_val: str):
            """
            Checks if the value is a low Celsius temperature that TMP36 captor
            can detect (int belonging to [-40; 16]).
            :param in_val:
            :type: str
            :raises: ValueError
            :rtype: int
            """
            val = int(in_val)
            if not (-40 <= val <= 16):
                raise ValueError("a low_tmp36_temp should be an int between"
                                 "-40 and 16")
            return val

        def high_tmp36_temp(in_val: str):
            """
            Checks if the value is a high Celsius temperature supportable by
            humans that the TMP36 captor can detect (int belonging to
            [17; 60]).
            :param in_val:
            :type: str
            :raises: ValueError
            :rtype: int
            """
            val = int(in_val)
            if not (17 <= val <= 60):
                raise ValueError("a high_tmp36_temp should be an int between"
                                 "17 and 60")
            return val

        def bool_from_int(in_val: str):
            """
            Checks if the value is an int and converts it to a boolean.
            :param in_val:
            :type: str
            :return: False if val == 0 else True
            :rtype: bool
            """
            return bool(int(in_val))

        # set-setting command
        subparsers["set_setting"].add_argument(
            "--user_mode",
            type=int,
            choices=[self.USER_MODE_AUTO, self.USER_MODE_OPEN,
                     self.USER_MODE_CLOSE]
        )
        subparsers["set_setting"].add_argument(
            "--time_check",
            type=valid_time
        )
        subparsers["set_setting"].add_argument(
            "--sunrise_hour",
            type=int,
            choices=range(0, 10)
        )
        subparsers["set_setting"].add_argument(
            "--sunset_hour",
            type=int,
            choices=range(14, 23)
        )
        subparsers["set_setting"].add_argument(
            "--low_light_threshold",
            type=lux
        )
        subparsers["set_setting"].add_argument(
            "--low_temp_threshold",
            type=low_tmp36_temp
        )
        subparsers["set_setting"].add_argument(
            "--high_temp_threshold",
            type=high_tmp36_temp
        )
        subparsers["set_setting"].add_argument(
            "--adapt_with_env_in_plain_day",
            type=bool_from_int
        )

        # log_setting command
        subparsers["log_setting"].add_argument(
            "name",
            type=str,
            choices=self.__config.keys()
        )

    def _init_communicator(self, suffix: str, args: dict):
        """
        Initialises the communicator class for the central unit.
        :param suffix: The suffix to append to "CentralUnitCommunicator",
        in order to get communicator class' name.
        :type: str
        :param args: The kwargs to pass to the communicator.
        :type: dict
        :return:
        :rtype: None
        """
        class_name = "CentralUnitCommunicator" + suffix
        comm_class = getattr(
            import_module(class_name),
            class_name
        )

        if not issubclass(comm_class, CentralUnitCommunicator):
            raise TypeError("Invalid suffix for central unit's communicator "
                            "class, the imported class isn't a "
                            "CentralUnitCommunicator's subclass")

        self._Communicator = comm_class(**args)
        self._get_cmd_fn = self._Communicator.get_cmds
        self._log_fn = self._Communicator.log

    def loop(self):
        """
            Main loop. Works until told otherwise by self.__loop().
            Catches errors and exits properly if needed.
            Will:
                -update the shutters
                -check if there is a command to execute
            :rtype: None
        """
        try:
            while self.__loop:
                self._update_shutters()
                self._run_commands()
        except Exception as e:
            self._proper_exit(1, e)
        else:
            self._proper_exit(0)

    def _update_shutters(self):
        """
        Updates the shutters according to the user_mode selected. Calls
        automatic_shutters when the user_mode is USER_MODE_AUTO.
        :return:
        :rtype: None
        """
        # Force open
        if self.__config["user_mode"] == self.USER_MODE_OPEN:
            self._open_shutters_if_closed()

        # Force close
        elif self.__config["user_mode"] == self.USER_MODE_CLOSE:
            self._close_shutters_if_opened()

        # Automatically choose (checks if we need to change current state
        # every self.__config['time_check'] seconds.
        elif (
                (self.__config["user_mode"] == self.USER_MODE_AUTO) and
                (
                    (time.time() - self.__last_check) >
                    self.__config['time_check']
                )
             ):
            self._log_fn("Automatically updating shutters", 'core/shutters',
                         "info")
            self._automatic_shutters(**self._check_luminosity_and_temp())
            self.__last_check = time.time()

    def _check_luminosity_and_temp(self):
        """Asks the arduino for the luminosity and the temperature
        :return: A dictionary containing the temp and the luminosity.
        :raises: ValueError
        :rtype: dict"""
        ans = self.arduino.ask(str(self.ARDUINO_GET_ENV), 2, line_ending="")
        temp = float(ans[0])
        if -40 <= temp <= 60:
            raise ValueError("Arduino returned an invalid temperature.")

        lum = float(ans[1])
        if lum < 0:
            raise ValueError("Arduino returned an invalid luminosity.")

        return {
            'temp': temp,
            'lum': lum
        }

    def _automatic_shutters(self, /, *, temp: int, lum: int):
        """Checks whether the shutters need to be opened or closed regarding
        the temperature, the time and the luminosity.
        :param temp: The outdoor temperature.
        :type: int
        :param lum: The outdoor luminosity.
        :type: int
        :note: See the .dia algorithm.
        :rtype: None"""
        hour = time.localtime().tm_hour
        day_moment = self._get_day_time(hour, lum)

        self._log_fn(
            f"{temp}°C, {lum}lux, {hour}th hour, " +
            ("plain day" if day_moment == self.PLAIN_DAY else "plain night"),
            'core/shutters',
            "debug"
        )

        if (  # Plain night = close 'em
                day_moment == self.PLAIN_NIGHT
                # Plain day = close 'em only if temperature requires it
                or
                (
                    # User asked to adapt to temperature ?
                    self.__config["adapt_with_env_in_plain_day"] and
                    (
                        (  # Too cold and dark sky ?
                            temp < self.__config['low_temp_threshold']
                            and
                            lum < self.__config["low_light_threshold"]
                        ) or
                        (  # Too hot while being at sun's midday ?
                            temp > self.__config['high_temp_threshold'] and
                            (abs(hour - (13 + time.daylight)) <= 4)
                        )
                    )
                )
                or
                # When shutters are closed, they should be closed for at least
                # one hour (it will avoid a "yoyo-shutters" problem).
                self._last_closed > (time.time() - 3600)
        ):
            self._close_shutters_if_opened()
        # Else open 'em !
        else:
            self._open_shutters_if_closed()

    def _get_day_time(self, hour: int, lum: int):
        """
        Will determine if we are at night or day. If we are at sunrise or
        sunset, it will use the luminosity and whether the shutters are
        opened or not to tell if it's considered night or day.
        :param hour: The current hour in 24h
        :type: int
        :param lum: The outdoor luminosity
        :type: int
        :return: The appropriate constant telling the day's time, PLAIN_DAY
        or PLAIN_NIGHT
        :rtype: int
        """
        sunrise_hour = self.__config["sunrise_hour"]
        sunset_hour = self.__config["sunset_hour"]

        # h belongs to ]sunset_hour; 23] or [0; sunrise_hour[: plain night
        if hour > sunset_hour or hour < sunrise_hour:
            return self.PLAIN_NIGHT

        # h belongs to ]sunrise_hour; sunset_hour[: plain day
        if sunset_hour > hour > sunrise_hour:
            return self.PLAIN_DAY

        low_lum = lum <= self.__config["low_light_threshold"]

        # h = sunrise_hour: depends on luminosity
        if hour == sunrise_hour:
            # if the luminosity is low at sunrise we consider that it's
            # still PLAIN_NIGHT
            # except if the shutters are already opened in order to avoid
            # avoid "Yo-Yo shutters". Once the shutters are opened, the day
            # is now fully started.
            if low_lum and self.__shutters_state == self.SHUTTERS_CLOSED:
                return self.PLAIN_NIGHT

            return self.PLAIN_DAY

        # h = sunset_hour: same
        if hour == sunset_hour:
            # at the contrary, if the luminosity is high at sunset we
            # consider that it's still PLAIN_DAY
            # except if the shutters are already closed
            if not low_lum and self.__shutters_state == self.SHUTTERS_OPENED:
                return self.PLAIN_DAY

            return self.PLAIN_NIGHT

    def _close_shutters_if_opened(self):
        """
        Will close the shutters if they are opened.
        :rtype: None
        """
        if self.__shutters_state != self.SHUTTERS_CLOSED:
            self._log_fn("Closing shutters", 'core/shutters', "status")

            self.arduino.ask(str(self.ARDUINO_CLOSE_SHUTTERS), line_ending="")
            self.__shutters_state = self.SHUTTERS_CLOSED

            # This is useful when we want to keep the shutters closed even
            # if the conditions require otherwise
            self._last_closed = time.time()

            self._log_fn('Done closing shutters', 'core/shutters', 'status')
            return
        self._log_fn('Shutters are already closed', 'core/shutters', 'debug')

    def _open_shutters_if_closed(self):
        """
        Will open the shutters if they are opened.
        :rtype: None
        """
        if self.__shutters_state != self.SHUTTERS_OPENED:
            self._log_fn('Opening shutters', 'core/shutters', "status")

            self.arduino.ask(str(self.ARDUINO_OPEN_SHUTTERS), line_ending="")
            self.__shutters_state = self.SHUTTERS_OPENED

            self._log_fn('Done opening shutters', 'core/shutters', 'status')
            return
        self._log_fn('Shutters are already opened', 'core/shutters', 'debug')

    def _run_commands(self):
        """
        Checks if there are commands and runs them if yes.
        :rtype: None
        """
        in_cmd = self._get_cmd_fn()
        if len(in_cmd):
            for cmd in in_cmd:
                self.parse_command(cmd)

    def _cmd_shutdown(self):
        """
        Command shutdown: sets self.__loop to False which will break the
        main loop.
        :rtype: None
        """
        self.__loop = False

    def _cmd_log_setting(self, name: str):
        """
        Will log the value of the given configuration parameter.
        :param name: The setting to log
        :type: str
        :rtype: None
        """
        self._log_fn(f"{name} is {str(self.__config[name])}", 'core/cmd',
                     'status')

    def _cmd_set_settings(self, **settings):
        """
        Will set the given settings to the given values.
        :param settings: The settings to change, the command is called using
        settings' name as arguments.
        :type: dict
        :rtype: None
        """
        for name in settings:
            val = settings[name]
            if val is not None:
                self.__config[name] = val
                self._log_fn(f"{name} now has {val} is now", 'core/cmd',
                             'status')

    def _cmd_force_update(self):
        """
        Force the CU to update the shutters in USER_MODE_AUTO.
        :rtype: None
        """
        self.__last_check -= self.__config['time_check'] + 1

    def parse_command(self, cmd: str):
        """
        Parses the given command using argparser, and executes it.
        :param cmd: The command to parse.
        :type: str
        :rtype: None
        """
        # Used in error messages, reminds the attempted command
        err_before = 'command "' + cmd + '": '

        in_command = cmd.split(" ")

        try:
            sanitized_output = vars(self.__argparser.parse_args(in_command))
        except argparseNoExit.ArgumentError as e:
            # Argparser raises ArgumentError on syntax error
            self._log_fn(f'{err_before} syntax: {e}',
                         'core/cmd', 'error')
            return
        except (TypeError, ValueError) as e:
            # ... and TypeError or ValueError on parameters error
            self._log_fn(f'{err_before} parameters: {e}', 'core/cmd',
                         'error')
            return

        # All method ran by commands should start with _cmd_
        fn_name = "_cmd_" + sanitized_output["command"]
        del sanitized_output["command"]
        # The rest of the sanitized_output dict is the parameters
        args = sanitized_output

        self._log_fn(f'running function {fn_name} with "{args}" for kwargs',
                     'core/cmd', 'debug')

        getattr(self, fn_name)(**args)

    def _proper_exit(self, code: int = 0, error: Exception = None):
        """
        Properly exit the CU (logs an error if needed, shutdowns connection s
        and then exits with the given exit code). This should be used over
        bare exit().
        :param code: The exit code, default 0.
        :type: int
        :param error: The Exception object if there is any, otherwise None.
        :type: Exception
        :return:
        """
        if error is not None:
            self._log_fn(str(error) + "\n" +
                         traceback.format_exc().strip(),
                         "core/init", 'error')

        self._log_fn("shutting down", 'core', 'status')

        try:
            del self._Communicator, self.arduino
        except AttributeError:
            pass

        exit(code)
