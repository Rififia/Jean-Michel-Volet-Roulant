#include <Adafruit_NeoPixel.h>
/**
   @file main.ino
   @description The main programm for the arduino-slave.
   @author Rififi
   @license CC-0
*/

// Change this (if you have more NeoPixels)
#define NUMBER_OF_SHUTTERS 3

//Put the right pins
/**
   @global
   @var RGBPins
   @description The pins for the RGB Led (Red, Green, Blue).
   @type {int[3]}
*/
int RGBPins[3] = {5, 6, 7},
    /**
       @global
       @var tempSensorPin
       @description The pin for the temperature sensor.
       @type {int}
    */
    tempSensorPin = A0,
    /**
       @global
       @var lightSensorPin
       @description Tha pin for the light sensor.
       @type {int}
    */
    lightSensorPin = A1;

// I guess you don't use Tinkercad
#define IN_TINKERCAD 1

// Stop changing here until told otherwise...
#define NONE 0
#define OPEN_SHUTTERS 8
#define CLOSE_SHUTTERS 16
#define SEND_INFOS 32

/**
    @class Shutter
    @description Represents a shutter, that can be opened and closed
*/
class Shutter {
  public:
    /**
       @public
       @constructor
       @description Checks that inPin is correct and initializes the attributes.
    */
    Shutter(int inPin, int inSize) {
      if (inPin > 13)
        return;

      pin = inPin;
      sizeOfShutter = inSize;
    }

    /**
       @method open
       @public
       @description Opens the shutter of howMany units. Put 0 for howMany unit or no argument to open completely.
       @param {int} howMany=0 From how many units do you want to open the shutter.
       @returns {bool} Wether the shutter is now fully opened or not.
    */
    bool open(int howMany = 0) {
      if (unitsClosed == 0) return true; // Fully opened
      if (howMany < 0) return false; // Not fully opened but error

      if (howMany == 0)
        howMany = unitsClosed; // We want to fully close it
      else // remaining option : howMany > 0
        howMany = min(howMany, unitsClosed); // In case the user specified something > the units that are down

      // NeoPixel only allows positive value for count argument, we need to go forward
      // and not backward.
      neoPixelObj.fill(0, unitsClosed - howMany, howMany);
      neoPixelObj.show();

      unitsClosed -= howMany;
      return unitsClosed == 0;
    }

    /**
        @method close
        @public
        @description Closes the shutter of howMany units. Put 0 for howMany unit or no argument to open completely.
        @param {int} howMany=0 From how many units do you want to close the shutter.
        @returns {bool} Wether the shutter is now fully closed or not.
        @see Shutter::open These functions' logic are the same.
    */
    bool close(int howMany = 0) {
      if (unitsClosed == sizeOfShutter) return true;
      if (howMany < 0) return false;

      if (howMany == 0)
        howMany = sizeOfShutter;
      else
        howMany = min(howMany, sizeOfShutter);

      // White is nearly invisible in Tinkercad, yellow flashes more.
      neoPixelObj.fill(neoPixelObj.Color(255, 255, 0), unitsClosed, howMany);
      neoPixelObj.show();

      unitsClosed += howMany;
      return unitsClosed == sizeOfShutter;
    }

    /**
       @method start
       @public
       @description Initialize the shutter (here using the Adafruit_NeoPixel libreary).
       @returns {void}
    */
    void start(void) {
      neoPixelObj = Adafruit_NeoPixel(sizeOfShutter, pin, NEO_GRB + NEO_KHZ800);
      neoPixelObj.begin();
      neoPixelObj.show();
    }

  private:
    /**
       @private
       @attribute pin
       @description The pin used to send the instructions to the shutter.
       @type {int}
    */
    int pin,
        /**
           @private
           @attribute sizeOfShutter
           @description The sizez of the shutter.
           @type {int}
        */
        sizeOfShutter,
        /**
           @private
           @attribute unitsClosed=0
           @description The number of shutter's units which are down (of how many units the shutter is closed).
           @type {int}
        */
        unitsClosed = 0;

    /**
       @private
       @attribute neoPixelObj
       @description The NeoPixel library used to simulate the shutter.
       @type {Adafruit_NeoPixel}
    */
    Adafruit_NeoPixel neoPixelObj;
};

/**
   @class StatusLed
   @description Represents the RGB led to output system's status
*/
class StatusLed {
  public:
    /**
       @public
       @constructor
       @description Initializes the pins, after checking them.
    */
    StatusLed(int inRGBPins[3]) {
      for (int i = 0; i < 3; i++) {
        if (inRGBPins[i] > 13)
          return;

        pinMode(inRGBPins[i], OUTPUT);
      }

      redP = inRGBPins[0];
      greenP = inRGBPins[1];
      blueP = inRGBPins[2];
    }

    /**
       @method out
       @public
       @description Turns on the RGB led using the given colors values.
       @note Using out() turns off the led.
       @param {int} r=0 Red value
       @param {int} g=0 Green value
       @param {int} b=0 Blue value
       @returns {void}
    */
    void out(int r = 0, int g = 0, int b = 0) {
      digitalWrite(redP, r);
      digitalWrite(greenP, g);
      digitalWrite(blueP, b);
    }

  private:
    /**
       @private
       @attribute redP
       @description The pin for red color.
       @type {int}
    */
    int redP,
        /**
           @private
           @attribute greenP
           @description The pin for green color.
           @type {int}
        */
        greenP,
        /**
           @private
           @attribute blueP
           @description The pin for blue color.
           @type {int}
        */
        blueP;
};

/**
   @class ShuttersManager
   @description Manages Shutter objects.
*/
class ShuttersManager {
  public:
    /**
       @public
       @constructor
       @description Initializes the attributes.
    */
    ShuttersManager(Shutter (&inShutterObjs)[NUMBER_OF_SHUTTERS], StatusLed inStatusLedObj) : ShutterObjs(inShutterObjs), StatusLedObj(inStatusLedObj) {}

    /**
       @public
       @method initShutters
       @description Initializes the shutters.
       @returns {void}
    */
    void initShutters(void) {
      for (int i = 0; i < NUMBER_OF_SHUTTERS; i++)
        ShutterObjs[i].start();
    }

    /**
       @public
       @method openAll
       @description Opens all the shutters.
       @returns {void}
    */
    void openAll() {
      StatusLedObj.out(255, 255);

#if IN_TINKERCAD
      delay(200);
#endif;

      for (int i = 0; i < NUMBER_OF_SHUTTERS; i++)
        ShutterObjs[i].open();
      StatusLedObj.out(0, 255);
    }

    /**
       @public
       @method closeAll
       @description Closes all the shutters.
       @returns {void}
    */
    void closeAll() {
      StatusLedObj.out(255, 255);

#if IN_TINKERCAD
      delay(200);
#endif;

      for (int i = 0; i < NUMBER_OF_SHUTTERS; i++)
        ShutterObjs[i].close();
      StatusLedObj.out(0, 0, 255);
    }

  private:
    /**
       @private
       @attribute ShutterObjs
       @description The list containing the Shutter objects.
       @type {Shutter[NUMBER_OF_SHUTTERS]}
    */
    Shutter ShutterObjs[NUMBER_OF_SHUTTERS];

    /**
      @private
      @attribute StatusLedObj
      @description The StatusLed object.
      @type {StatusLed}
    */
    StatusLed StatusLedObj;
};


/**
   @function receiveOrder
   @description Receive the commands from Serial ports, returns the int corresponding to the order:
   @note 0 = NONE
   @note 8 = OPEN_SHUTTERS
   @note 16 = CLOSE_SHUTTERS
   @note 32 = SEND_INFOS
   @returns {int} The command's code.
*/
int receiveOrder() {
  //checks whether there is anything to read
  if (Serial.available() > 0) {
    /**
       @var orderId
       @description The command id received.
       @type {long}
    */
    int orderId = Serial.parseInt();

    if (orderId > 0 && orderId % 2 == 0) // valid or not ?
      return orderId;
    else
      Serial.println("ERROR: invalid value received, should be an int > 0 and divisible by 2.");
  }

  return NONE;
}


/**
   @function getTemperature
   @description Gets the current temperature in Celsius.
   @note Using the TMP36 sensor : in +5V, out = Voltage.
   @return {float} The temperature in Celsius.
*/
float getTemperature() {
  /**
     @var sensorInput
     @description A 0-1023 value telling the voltage, given by the sensor.
     @type {int}
  */
  int sensorInput = analogRead(tempSensorPin);

  /**
     @var realMiliVoltage
     @description The real voltage in mV sent by the sensor, using proportionnality (5000 / 1024 ~= 4.8828125)
     @var {float}
  */
  float realMiliVoltage = sensorInput * 4.8828125;

  return realMiliVoltage / 10 - 50; // Converting Voltage to Celcius (using the data table from TMP36 temperature) and substracting the offset.
}

/**
   @function getLight
   @description Gets the current light intensity, in percentage.
   @note Using a classical Arduino's photoresistor and a 10k Ohm resistor.
   @returns {float} The light intensity in "percentage" (0 is all dark, 100 is full light = sun at the maximum above), corresponds to the potentiometer in Tinkercad to simulate the luminosity.
*/
float getLight() {
  /**
     @var sensorInput
     @description A 54 - 974 value (in our case) telling the voltage (which differs according to the resistance of the photoresistor), sent by the sensor.
     @type {int}
  */
  int sensorInput = analogRead(lightSensorPin);

  if (sensorInput == 54) // Some arbitrary values
    return 0;
  if (sensorInput == 974)
    return 100;

  return 0.0012 * exp(0.0116 * sensorInput); // Calibrating to a percentage using a trend function.
}

/**
   @function sendData
   @description Gets the date from sensors and then print it (waits until it's possible to print it for).
   @returns {void}
*/
void sendData() {
  while (Serial.availableForWrite() < 30); // Waiting for the receiver to be available
  Serial.print(getTemperature());
  Serial.print(";");
  Serial.println(getLight());
}

// ...continue to change here...
/**
   @global
   @var ShutterObjs
   @description The list containing the Shutter objects.
   @type {Shutter[NUMBER_OF_SHUTTERS]}
*/
Shutter ShutterObjs[NUMBER_OF_SHUTTERS] = {
  Shutter(2, 8), //pin, size
  Shutter(3, 10),
  Shutter(4, 16)
};
// ...and defintely stop changing from here!


/**
    @global
    @var StatusLedObj
    @description The StatusLed object.
    @type {StatusLed}
*/
StatusLed StatusLedObj = StatusLed(RGBPins);

/**
   @global
   @var ShuttersManagerObj
   @description The ShuttersManager object.
   @type {ShuttersManager}
*/
ShuttersManager ShuttersManagerObj = ShuttersManager(ShutterObjs, StatusLedObj);


/**
   @function setup
   @description Initializes objects and status led.
   @returns {void}
*/
void setup() {
  StatusLedObj.out(255);

#if IN_TINKERCAD
  delay(200); // For demo purpose
#endif;

  // Serial communication:
  Serial.begin(9600);
  Serial.setTimeout(200); // It should not in most case wait for the host, the data will be retrieved from the buffer.

  // Sensors:
  pinMode(tempSensorPin, INPUT);
  pinMode(lightSensorPin, INPUT);

  // Shutters' manager:
  ShuttersManagerObj.initShutters();
  ShuttersManagerObj.openAll(); // Shutters should be all opened for initialisation (easier)
}

/**
   @function loop
   @description Main programm. Receive the orders and execute the requested command.
   @returns {void}
*/
void loop() {
  /**
     @var cmdId
     @description The command ID received by receiveOrder.
     @type {int}
  */
  int cmdId = receiveOrder();

  switch (cmdId) {
    case NONE:
      break;

    case OPEN_SHUTTERS:
      ShuttersManagerObj.openAll();
      break;

    case CLOSE_SHUTTERS:
      ShuttersManagerObj.closeAll();
      break;

    case SEND_INFOS:
      sendData();
      break;

    default:
      Serial.print("ERROR: unknown command id: ");
      Serial.println(cmdId);
  }

#if IN_TINKERCAD
  delay(250);
#endif;
}