from argparse import *

class ArgumentParserNoExit(ArgumentParser):
    def error(self, message: str):
        raise ValueError(message)
