import CentralUnit
import argparse

if __name__ == "__main__":
    available_errors = {
        "error": 1,
        "warning": 2,
        "status": 4,
        "debug": 8
    }

    communicators = {
        "file": {
            "suffix": "File",
            "args": {
                "input_file_path": 'CentralUnit.stdin',
                "output_file_path": 'CentralUnit.log',
                # 0 = CR_LF, 1 = LF, 2 = CR
                "line_end": 1,
                "log_types_on": []
            }
        }
    }

    parser = argparse.ArgumentParser(
        description="Entry point to start the central-unit.",
        exit_on_error=True
    )

    parser.add_argument(
        '--time_check',
        default=600,
        type=int,
        help="the time in seconds between checks of temperature, default 600"
    )

    parser.add_argument(
        '--communication_type',
        default="file",
        type=str,
        choices=communicators.keys(),
        help="Way to communicate with the CentralUnit"
    )

    parser.add_argument(
        '--log_levels',
        default=1 | 2 | 4 | 8,
        type=int,
        help="Way to communicate with the CentralUnit"
    )
    parser.add_argument(
        '--max_cmd_in_queue',
        default=10,
        type=int,
        help="Way to communicate with the CentralUnit"
    )

    parser.add_argument(
        '--port',
        default="COM1",
        help="Arduino's COM port, default COM1"
    )
    parser.add_argument(
        '--baudrate',
        type=int,
        default=9600,
        choices=[
            50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800, 9600,
            19200, 38400, 57600, 115200
        ],
        help="baudrate to communicate with Arduino, default 9600"
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=1,
        help="timeout for the serial comm. with the Arduino in s, default 1s"
    )

    args = vars(parser.parse_args())
    ar_serial_args = {
        'port': args['port'],
        'baudrate': args['baudrate'],
        'timeout': args['timeout']
    }
    communicator = communicators[args["communication_type"]]
    communicator['args']['max_cmd_in_queue'] = args['max_cmd_in_queue']

    for name in available_errors:
        if args['log_levels'] & available_errors[name]:
            communicator['args']['log_types_on'].append(name)

    CU = CentralUnit.CentralUnit(time_check=args['time_check'],
                                 communicator_suffix=communicator['suffix'],
                                 communicator_args=communicator['args'],
                                 arduino_serial_args=ar_serial_args)
    CU.loop()
