# Jean Michel Volet Roulant
This is a school project (and therefore has more the goal to train us than to make a real thing, objects like the curtains are just simulated/represented :-)).
Jean Michel Volet Roulant is a home-automation system to automatically control curtains, according to the weather, the time, and the wills of inhabitants.
The inhabitants can ask specific requirements using a control panel (which is simulated here in Python). A Python program (the Home Automation Central Unit) will then take in account these requirements amongst with the environment-data gave by the Arduino slave, and accordingly open or close the curtains through the Arduino slave.

## Division of the project
- In arduino-slave you will find the code and the schemas for the circuits that sends the sensor's data and opens/close the curtains. I didn't use a Rasberry for the simple reason that I don't own one and didn't find a suitable emulator.
- In home-automation-central-unit you will find the Python code that makes all the decisions. It was not directly put into the Arduino because of Arduino's limitations and my limited knowledge of it.
- In simulated-control-panel you will find the Python code to simulate the control panel (visible by inhabitants) and the connection with the central unit.