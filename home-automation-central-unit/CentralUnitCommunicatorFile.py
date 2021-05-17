from CentralUnitCommunicator import CentralUnitCommunicator

CUCParent = CentralUnitCommunicator


class CentralUnitCommunicatorFile(CUCParent):
    LINE_END_CR_LF = 0
    LINE_END_LF = 1
    LINE_END_CR = 2
    LINE_ENDING_CHARACTERS = ["\r\n", "\n", "\r"]

    def __init__(self,
                 log_types_on=None,
                 max_cmds_in_queue: int = 10,
                 input_file_path: str = 'CentralUnit.stdin',
                 output_file_path: str = 'CentralUnit.log',
                 line_end: int = LINE_END_LF):
        if log_types_on is None:
            log_types_on = ['error', 'warning', 'status', 'debug']
        self._log_types_on, self._max_cmd = CUCParent.check_attrs(
            log_types_on, max_cmds_in_queue)

        line_end = int(line_end)
        if line_end not in [self.LINE_END_CR_LF, self.LINE_END_LF,
                            self.LINE_END_CR]:
            raise ValueError("invalid line_end")
        self._line_end = line_end

        open(input_file_path, 'w').close()
        self._input_file_path = input_file_path

        open(output_file_path, 'a').close()
        self._output_file_path = output_file_path

    def __del__(self):
        open(self._input_file_path, 'w').close()

    def get_cmd(self) -> list:
        input_file = open(self._input_file_path, 'r', encoding="UTF8",
                          newline=self.get_line_end())

        cmd = []

        for line in input_file:
            line = line.strip()
            if len(line.strip()):
                if (len(cmd) + 1) > self._max_cmd:
                    self.log(f'maximum of {str(self._max_cmd)} commands in ' +
                             'queue exceeded', 'communicator', 'warning')
                    break
                cmd.append(line)

        if len(cmd) > 0:
            open(self._input_file_path, "w")

        input_file.close()

        return cmd

    def get_line_end(self):
        return self.LINE_ENDING_CHARACTERS[self._line_end]

    def log(self, msg: str, source: str, log_type: str):
        if len(msg) == 0 or len(source) == 0 or len(log_type) == 0:
            raise ValueError("no string should be empty")

        if log_type in self._log_types_on:
            out = open(self._output_file_path, 'a', encoding="UTF8",
                       newline=self.get_line_end())
            out.writelines([
                self._generate_log_output(msg, source, log_type) +
                self.get_line_end()
            ])
            out.close()
