# See  https://pythonhosted.org/pyserial/
import serial


# inheritance ?
class ArduinoSerial:
    """
        Simple class to communicate with an Arduino, just a single input/output.
    """

    def __init__(self, /, *, programmed_for_as=False,
                 port='COM1', baudrate=9600, timeout=1, log_fn=print,
                 **kwargs) -> None:
        self.serial = serial.Serial(port=port, baudrate=baudrate,
                                    timeout=timeout, **kwargs)

        self.compatible_with_AS = programmed_for_as

        if not callable(log_fn):
            raise TypeError("log_fn must be callable")
        self._log_fn = log_fn

        if not programmed_for_as:
            return

        # Arduino restarts upon serial connection (which may good for us,
        # all programs are then initialised together), so wee need to wait for
        # it (hence the 30s timeout)
        self._log_fn("Waiting for Arduino's CONNECT")
        if self.read_line(timeout=30) != "CONNECT":
            raise ConnectionError("failed to connect to Arduino")
        self._log_fn("CONNECT received")

        # Telling the Arduino she's not talking to a wall
        self._log_fn("Sending signal")
        self.send("1", line_ending="")
        self._log_fn('Sent a signal')

        # The Arduino is slow, and must be the last one to talk.
        self._log_fn("Waiting for READY")
        if self.read_line() != "READY":
            raise ConnectionError("Arduino wasn't ready")
        self._log_fn("READY received !")

    def __del__(self) -> None:
        self.end()

    def start(self) -> None:
        self.serial.open()

    def end(self) -> None:
        try:
            self.serial.close()
        except AttributeError:
            pass

    def send(self, string, /, *, line_ending="\r\n", encoding='ASCII') -> None:
        self.serial.write(bytes(string + line_ending, encoding))

    def read_as_string(self, *, encoding='ASCII', **kwargs) -> str:
        """
        Same as read_bytes but decodes bytes into a string, using by default
        ASCII encoding.
        ::param encoding=ASCII string The encoding name to decode.
        ::kwargs Arguments for read_bytes.
        ::see read_bytes for keywords argument.
        ::returnType str"""
        return self.read_bytes(**kwargs).decode(encoding)

    def read_bytes(self, *, number=None, timeout: int = -1) -> bytes:
        """
        Reads a specific number of bytes, or everything in the buffer if None
        is specified. Will wait until timeout occur if a specific number of
        bytes is required but not found in the buffer.
        ::param number=None The number of bytes to read, None = read everything
        ::param timeout=False Sets the timeout, False = keeps the timeout set
        at initialisation, None = no timeout, any float = timeout in seconds.
        ::returnType bytes
        """
        old_t_out = None
        if timeout != -1:
            old_t_out = self.serial.timeout
            self.serial.timeout = timeout

        string_in = (self.serial.read_all() if number is not None
                     else self.serial.read(number))

        if timeout != -1:
            self.serial.timeout = old_t_out

        return string_in

    def read_line(self, *, max_size=None, encoding="ASCII",
                  timeout: int = -1) -> str:
        """Returns a complete line, without \r\n, read from the buffer (if
        there is any until timeout occur or maxSize is exceeded). You can set a
        specific timeout with the timeout parameter.
        ::param timeout mixed Put False to keep the original one (set at
        initialisation), None to wait infinitely or otherwise the timeout in
        seconds."""
        old_t_out = None
        if timeout != -1:
            old_t_out = self.serial.timeout
            self.serial.timeout = timeout

        input_str = self.serial.read_until(expected=b"\r\n",
                                           size=max_size).decode(encoding)

        if timeout != -1:
            self.serial.timeout = old_t_out

        if input_str[-2:] == "\r\n":
            return input_str[0:-2]

    def ask(self, msg: str = "", data_num_expected: int = 0, **send_kwargs):
        """ Only if Arduino is programmed to be in accordance with the function
        Sends msg, and then wait for an answer, either to check if there is an
        error or to return the answer. Arduino's answer should be in the format
        "data1;data2;...". In case of an error, the Arduino must send
        "ERROR;error msg"."""
        if not self.compatible_with_AS:
            return NotImplementedError(
                "Arduino isn't compatible with AS's special methods.")

        self.send(msg, **send_kwargs)

        ans = self.read_line()

        if ans is not None:
            info = ans.split(";")
            if len(info) >= 2 and info[0] == "ERROR":
                raise ConnectionError("Arduino returned error : " + info[1])
            if len(info) == data_num_expected:
                return info
            raise ValueError("Invalid value received from arduino: " + ans)

        if data_num_expected > 0:
            raise TimeoutError("Arduino didn't return anything in time")


if __file__ == "__main__":
    import time

    arduino = ArduinoSerial(inPort="COM3")
    # Arduino sometimes needs some rest after connection, and the program
    # don't wait for it here
    time.sleep(2)
    arduino.send("Hello world !")
    print(arduino.read_line())
