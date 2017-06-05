#include "SleepyPi2.h"
#include <Time.h>
#include <LowPower.h>
#include <Wire.h>

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
void setup() {
  // Turn the Serial Protocol ON
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  Serial.println("Start..");
  delay(50);
  readCommand = false;
  start = false;
  parse = false;
  mySerial.begin(9600);
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
        startPi ();
      }
      if (value == "000000") {
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
