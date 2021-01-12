# Jean Michel Volet Roulant
This is a school project.
Jean Michel Volet Roulant is a home-automation system to automatically control curtains, according to the weather, the time, and the wills of inhabitants.
The inhabitants can ask specific requirements using an interface (which is emulated here in Python), and a Python program will then take in account these requirements, the environment-data gave by the Arduino slave, and then will properly open or close the curtains through the Arduino slave.

##Division of the project
In arduino-slave you will find the code and the schemas for the circuits that sends the data and opens/close the curtains. The brain was not written in Arduino because of Arduino’s limitation.
In command-unit you will find the Python code that makes the decisions.
In emulated-interface you will find the Python code to emulate the end-user interface and the connection with the command-unit. It will also gives something to emulate the Arduino slave, sending data (that you can change) and displaying the order received from the command-unit.
