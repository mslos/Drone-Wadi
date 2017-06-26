#include "SleepyPi2.h"
#include <Time.h>
#include <LowPower.h>
#include <PCF8523.h>
#include <Wire.h>
#include <SoftwareSerial.h>

#define TIMEOUT_MSEC 300*1000

int green = 6;
int yellow = 5;

SoftwareSerial xBeeSerial(9, 10); // Serial for Xbee RX, TX

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
String iden;
bool pi_running;
unsigned int timeSinceLastContact;


void setup() {
  // Turn the Serial Protocol ON
  Serial.begin(9600); //Serial communication to RasPi
  while (!Serial) {
    ; // wait for serial port to connect. Just in case
  }
  Serial.println("Start..");
  delay(50);
  readCommand = false;
  start = false;
  parse = false;
  xBeeSerial.begin(9600);
  xBeeSerial.println("Hello, world?");
  SleepyPi.enablePiPower(true);
  pinMode(green, OUTPUT);
  pinMode(yellow, OUTPUT);
  timeSinceLastContact = millis();
}

void loop() {
  SleepyPi.enableExtPower(true);
  char	theChar;
  command = ""; //reset command
  value= ""; //reset value of command
  iden="";

  if (xBeeSerial.available()) {
    theChar=xBeeSerial.read();
    reader(start, parse, dataInputBuffer, theChar);
    if (parse){
      parser(iden,command,value,dataInputBuffer,dataIndex);
      parse = false;
      readCommand = true;
    }
  }

  if (readCommand && (iden == ID)){
    timeSinceLastContact = millis();
    xBeeSerial.print("%"+ID+" "+command+" "+value+'\r'+'\n');

    if (command == "POWR"){
      if (value == "00000?"){
        pi_running = SleepyPi.checkPiStatus(false);
        if (pi_running == true){
          value = "000001";
        }
        else {
          value = "000000";
        }
        xBeeSerial.print("%"+ID+" "+command+" "+value+'\r'+'\n');
      }
      else if (value == "000001"){
        startPi();
      }
      else if (value == "000000") {
        shutPi();
      }
    }

    if (command == "RSET"){
      resetCamera();
    }
    if (command == "IDEN"){
      xBeeSerial.print("%"+ID+" "+command+" 000"+ID+'\r'+'\n');
    }
    readCommand = false;
  }

  //timeot if no communication happened for a long time
  if (millis()-timeSinceLastContact > TIMEOUT_MSEC) {
    timeSinceLastContact=millis();
    shutPi();
  }

  //reads from serial input and sends it via Xbee
  if (Serial.available()){
    xBeeSerial.write(Serial.read());
  }

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

//Parser function: Parse the data buffer into command, ID and value
void parser (String &iden, String &command, String &value, char dataInputBuffer[], int stringLenth){
  char valueBuffer[6] = {}; //max size of value is 6 bytes
  int valueIndex = 0;

  for (int x =1; x<= stringLength; x++){
    if (x<4){ //Parse ID
      iden = iden+dataInputBuffer[x];
    }
    else if (x<9 && x>4){ //Parse command
      command = command+dataInputBuffer[x];
    }
    else if ((dataInputBuffer[x]!=' ')){ //preprocess value
      valueBuffer[valueIndex]=dataInputBuffer[x];
      valueIndex++;
    }
  }
  Serial.println(valueBuffer);
  Serial.println(dataInputBuffer);
  for (int c=0; c<=5; c++){
    if (valueBuffer[c]){ //parse value
      value = value + valueBuffer[c];
    }
    else{ //prepend 0 to value for every NULL in valueBuffer
      value = '0'+value;
    }
    Serial.println(value);
  }
  Serial.print("Parser: Command is ");
  Serial.println(command);
  Serial.print("Parser: Value is ");
  Serial.println(value);
  Serial.print("Parser: ID is ");
  Serial.println(iden);
}

//Reader function: Starts appending incoming characters to a data buffer when ':' appears
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
    Serial.println("Reader: ");
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
  //masterOff();
  //masterOn();
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
