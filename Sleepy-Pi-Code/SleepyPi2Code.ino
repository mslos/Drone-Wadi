#include "SleepyPi2.h"
#include <Time.h>
#include <LowPower.h>
#include <PCF8523.h>
#include <Wire.h>
#include <SoftwareSerial.h>

int green = 6;
int yellow = 5;

SoftwareSerial mySerial(9, 10); // RX, TX

int dataIndex = 0;
char dataInputBuffer[32];
char valueBuffer[7];
String ID = "001"; //The ID of the Camera
bool start;
bool parse;
bool readCommand;
String command;
int stringLength;
String value;
bool pi_running;


#define RPI_POWER_TIMEOUT_MS     9000    // in ms - so this is 6 seconds
#define TIME_INTERVAL_SECONDS    0
#define TIME_INTERVAL_MINUTES    2
#define TIME_INTERVAL_HOURS      0
#define TIME_INTERVAL_DAYS       0

tmElements_t powerUpTime;

void alarm_isr()
{
}

void setup() {

  Serial.begin(9600); //Serial for debugging

  // set alarm time
  powerUpTime.Second = TIME_INTERVAL_SECONDS;
  powerUpTime.Minute = TIME_INTERVAL_MINUTES;
  powerUpTime.Hour   = TIME_INTERVAL_HOURS;
  powerUpTime.Day    = TIME_INTERVAL_DAYS;

  delay(1000);

  SleepyPi.enableWakeupAlarm();
  SleepyPi.setAlarm(powerUpTime);


  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  Serial.println("Start..");
  delay(50);
  readCommand = false;
  start = false;
  parse = false;
  mySerial.begin(9600); //software serial for communication with Xbee
  mySerial.println("Hello, world?");
  SleepyPi.enablePiPower(true);
  pinMode(green, OUTPUT);
  pinMode(yellow, OUTPUT);
}

void loop() {
  SleepyPi.enableExtPower(true);
  char	theChar;
  command = ""; //reset command
  value=""; //reset value of command
  if (mySerial.available()){
    theChar=mySerial.read();
    reader(start, parse, dataInputBuffer, theChar);
    if (parse){
      parser(command,value,dataInputBuffer,dataIndex);
      parse = false;
      readCommand = true;
    }
  }
  if (readCommand){
    mySerial.print("%"+ID+" "+command+" "+value+'\r'+'\n');
    if (command == "POWR"){
      if (value == "00000?"){
        pi_running = SleepyPi.checkPiStatus(false);
        if (pi_running == true){
          value = "000001";
        }
        else{
          value = "000000";
        }
        mySerial.print("%"+ID+" "+command+" "+value+'\r'+'\n');
      }
      if (value == "000001"){
        //wake up RPi
        startPi ();
      }
      if (value == "000000") {
        //shut down RPi
        shutPi();
      }
    }
    if (command == "RSET"){
      resetCamera();
    }
    if (command == "IDEN"){
      mySerial.print("%"+ID+" "+command+" 000"+ID+'\r'+'\n');
    }
    readCommand = false;
  }
  if (Serial.available()){
    mySerial.write(Serial.read());
  }



  // Enable inturrupt
  attachInterrupt(0, alarm_isr, FALLING);		// Alarm pin


  //TODO: Do you need to reset the alarm? What is ackAlarm?
  //    SleepyPi.ackAlarm();
  //    SleepyPi.enableWakeupAlarm();
  //    SleepyPi.setAlarm(powerUpTime);

  // Powerdown sleepy pi and wake up when pin is low
  SleepyPi.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);

  // Disable interrupt once pi has powered up
  detachInterrupt(0);



}

//function to turn on RaspberryPi
void startPi (){
  pi_running = SleepyPi.checkPiStatus(false);
  if  (pi_running == false) {
    SleepyPi.enablePiPower(true);
    SleepyPi.enableExtPower(true);
    delay(50);
    Serial.println("OPEN PI");
  }
}
//function to turn off RaspberryPi
void shutPi (){
  pi_running = SleepyPi.checkPiStatus(false);
  if  (pi_running == true) {
    SleepyPi.piShutdown(true);
    SleepyPi.enableExtPower(true);
    SleepyPi.enablePiPower(false);
    delay(50);
    Serial.println("SHDN PI");
  }
}
//parser function. Parse the data buffer into command and value
void parser (String &command, String &value, char dataInputBuffer[], int stringLenth){
  char valueBuffer[6] = {};
  int valueIndex = 0;
  for (int x =1; x<= stringLength; x++){
    if (x<5){
      command= command+dataInputBuffer[x];
    }
    else if ((dataInputBuffer[x]!=' ')){
      valueBuffer[valueIndex]=dataInputBuffer[x];
      valueIndex++;
    }

  }
  Serial.println(valueBuffer);
  Serial.println(dataInputBuffer);
  for (int c=0; c<=5; c++){

    if (valueBuffer[c]){
      value = value + valueBuffer[c];
    }
    else{
      value = '0'+value;
    }
    Serial.println(value);
  }
  Serial.println (value);
}

//reader function. Starts appending messages to a data buffer when ':' appears
void reader (bool &start, bool &parse, char dataInputBuffer[], char theChar){
  if (theChar == ':'){ //start reading the string if the incoming byte is ":"
    dataIndex = 0;
    start = true;
  }
  if ((theChar == 0x0d)|| (theChar == 0x0a) || (dataIndex > 31)){ // if incoming byte is CR then stop reading the string	// null terminate the string
    stringLength = dataIndex;
    if (dataIndex != 0){
      parse = true;
    }
    dataIndex=0;
    start = false;
  }
  else if (theChar >= 0x20 && start){
    dataInputBuffer[dataIndex]=theChar;
    dataIndex++;
  }
}

void resetCamera() {
  pi_running = SleepyPi.checkPiStatus(false);
  if (pi_running == true){
    shutPi();
  }
  masterOff();
  masterOn();
  Serial.print("Reset Camera");
}

void masterOn() {
  turnSetup(green,yellow);
  delay(50);
  turnOff(green, yellow);
  delay(50);
  turnSetup(green,yellow);
  delay(50);
  turnOn(green, yellow);
}

void masterOff() {
  turnSetup(green,yellow);
  delay(50);
  turnOff(green, yellow);
}

void masterSetup() {
  turnSetup(green,yellow);
}

void turnOff(int green, int yellow) {
  digitalWrite(green, HIGH);
  digitalWrite(yellow, LOW); //default state of yellow is connected to COM
}

void turnOn(int green, int yellow) {
  digitalWrite(green, LOW);
  digitalWrite(yellow,LOW);
}

void turnSetup(int green, int yellow) {
  digitalWrite(green, LOW);
  digitalWrite(yellow, HIGH);
}
