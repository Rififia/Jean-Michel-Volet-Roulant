import abc
import time


class CentralUnitCommunicator(abc.ABC):
    """
    The abstract class CentralUnitCommunicator, defines how Communicators
    for the CentralUnit should work.
    """
    @abc.abstractmethod
    def __init__(self, log_types_on: list, max_cmds_in_queue: int):
        """Initializes the connections to receive commands and send logs, and
        sets the maximum command in queue allowed.
        :param log_types_on: The log types (error, warning ...) that will
        be used.
        :type: list
        :param max_cmds_in_queue: The maximum number of commands in queue if
        commands can be queued.
        :type: int
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def __del__(self):
        """
        Flushes input buffer and closes the connection.
        :rtype: None
        """
        pass

    @abc.abstractmethod
    def get_cmds(self) -> list:
        """Return received commands in a list, with a maximum of self.max_comm
        and_in_queue, the exceeding is discarded.
        :return: The list of received commands, one command per item.
        :rtype: list
        """
        pass

    @abc.abstractmethod
    def log(self, msg: str, source: str, log_type: str):
        """Logs a message if the log_type is enabled.
        :param msg: The message to log.
        :type: str
        :param source: The source from which the message come from.
        :type: str
        :param log_type: The type of the log (error, warning, etc.)
        :type: str
        :note: see self._generate_log_output for the log format.
        :rtype: None"""
        pass

    @staticmethod
    def check_attrs(log_types_on: list, max_cmd_in_queue: int):
        """Checks attributes for subclasses, these attributes are gave when
        instantiating the class.
        :param log_types_on:
        :type: list
        :param max_cmd_in_queue:
        :type: list
        :rtype: tuple"""
        if not isinstance(log_types_on, list):
            raise TypeError("log_types_on must be a list")

        max_cmd_in_queue = int(max_cmd_in_queue)
        if max_cmd_in_queue <= 1:
            raise ValueError("max_cmd_in_queue must be an int > 1")

        return log_types_on, max_cmd_in_queue

    @staticmethod
    def _generate_log_output(msg: str, source: str, log_type: str) -> str:
        """Generates a log output. The format is:
        YY-mm-dd:HH:MM:SS: (source/type) message
        :param msg: The message to log.
        :type: str
        :param source: The source from which the message come from.
        :type: str
        :param log_type: The type of the log (error, warning, etc.).
        :type: str
        :return: Formatted message.
        :rtype: str"""
        return f"{time.strftime('%Y-%m-%d:%H:%M:%S')}: " + \
               f"({source}/{log_type}) {msg}"
