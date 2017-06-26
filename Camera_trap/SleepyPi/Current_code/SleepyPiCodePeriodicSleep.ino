#include "SleepyPi2.h"
#include <Time.h>
#include <LowPower.h>
#include <PCF8523.h>
#include <Wire.h>

//Software serial from https://github.com/arduino/Arduino/tree/master/hardware/arduino/avr/libraries/SoftwareSerial
#include <SoftwareSerial.h> 

#define TIMEOUT_MSEC 300000
#define CAMERA_ID String("002")
#define FIRMWARE_VERSION String("0.4 Trans, timeout and periodic sleep")

int green = 6;
int yellow = 5;

//Uses software serial from Github with extra functions
SoftwareSerial xBeeSerial(9, 10); // Serial for Xbee RX, TX

int dataIndex = 0;
char dataInputBuffer[32];
char valueBuffer[7];
String ID = CAMERA_ID; //The ID of the Camera
bool start;
bool parse;
bool readCommand;
String command;
int stringLength;
String value;
String iden;
bool pi_running;
unsigned long timeSinceLastContact;

//Variables from Sleepy Pi WakeUpPeriodically example
bool droneInViccinity;
tmElements_t tm;
const char *monthName[12] = {
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
};

void setup() {
  // Turn the Serial Protocol ON
  Serial.begin(9600); //Serial communication to RasPi
  while (!Serial) {
    ; // wait for serial port to connect. Just in case
  }
  Serial.print("Starting camera trap Arduino firmware version: ");
  Serial.println(FIRMWARE_VERSION);

  delay(50);

  readCommand = false;
  start = false;
  parse = false;
  xBeeSerial.begin(9600);

  xBeeSerial.print("Starting camera trap Arduino firmware version: ");
  xBeeSerial.println(FIRMWARE_VERSION);

  SleepyPi.enablePiPower(true);
  pinMode(green, OUTPUT);
  pinMode(yellow, OUTPUT);
  timeSinceLastContact = millis();

  SleepyPi.rtcInit(true);
  droneInViccinity = false;
  // Default the clock to the time this was compiled.
  // Comment out if the clock is set by other means
  // ...get the date and time the compiler was run
  if (getDate(__DATE__) && getTime(__TIME__)) {
      // and configure the RTC with this info
      SleepyPi.setTime(DateTime(F(__DATE__), F(__TIME__)));
  } 
  
  printTimeNow();   
}

void loop() {

  SleepyPi.enableExtPower(true);
  char	theChar;
  command = ""; //reset command
  value= ""; //reset value of command
  iden="";
  Serial.print("Value of drone in viccinity is ");
  Serial.println(droneInViccinity);
  Serial.print("Value of millis is ");
  Serial.println(millis());
  
  if(!droneInViccinity) {
    lowPowerMode();
  }

  if (xBeeSerial.available()) {
    Serial.println("Character was available");
    droneInViccinity = true;
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
    else if (command == "RSET"){
      droneInViccinity = false;
      resetCamera();
    }
    else if (command == "IDEN"){
      droneInViccinity = true;
      xBeeSerial.print("%"+ID+" "+command+" 000"+ID+'\r'+'\n');
    } else if (command == "LOPW") {
       droneInViccinity = false;
    }
    readCommand = false;
  }

  //timeot if no communication happened for a long time
  if ((millis()-timeSinceLastContact > TIMEOUT_MSEC)) {
    Serial.println("Timeout occured");
    timeSinceLastContact=millis();
    //renew sleep mode
    droneInViccinity = false;
    //turn off raspberry pi
    if(SleepyPi.checkPiStatus(false)) {
      //shutPi();
    }
  }

  //reads from serial input and sends it via Xbee
  if (Serial.available()){
    xBeeSerial.write(Serial.read());
  }

}


void alarm_isr()
{
    // Just a handler for the alarm interrupt.
    // You could do something here

}

void lowPowerMode() {
  xBeeSerial.stopListening();
  Serial.println(SleepyPi.rtcIsRunning() ? "PCF8523 connection successful" : "PCF8523 connection failed");
  Serial.println("Sleepy pi is going to sleep.");
  printTimeNow();  
  delay(50);
  SleepyPi.enableExtPower(false);
  delay(50);
  SleepyPi.rtcClearInterrupts();
  // Allow wake up alarm to trigger interrupt on falling edge.
  attachInterrupt(0, alarm_isr, FALLING);    // Alarm pin
  // Set the Periodic Timer
  SleepyPi.setTimer1(eTB_SECOND, 60);
  delay(500);
  // Enter power down state with ADC and BOD module disabled.
  // Wake up when wake up pin is low.
  SleepyPi.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  // Disable external pin interrupt on wake up pin.
  detachInterrupt(0);
  SleepyPi.ackTimer1();
  SleepyPi.enableExtPower(true);
  delay(500);
  xBeeSerial.listen();
  delay(500);
  Serial.print("isListening() gives ");
  Serial.println(xBeeSerial.isListening());
  Serial.print("Overflow flag is ");
  Serial.println(xBeeSerial.overflow());
  Serial.println("Sleepy pi woke up from sleep.");
  printTimeNow();  
  delay(500);
  return;
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

// **********************************************************************
// 
//  - Helper routines from John Atkins Sleepy Pi Example Periodic Sleep
//
// **********************************************************************
void printTimeNow()
{
    // Read the time
    DateTime now = SleepyPi.readTime();
    
    // Print out the time
    Serial.print("Ok, Time = ");
    print2digits(now.hour());
    Serial.write(':');
    print2digits(now.minute());
    Serial.write(':');
    print2digits(now.second());
    Serial.print(", Date (D/M/Y) = ");
    Serial.print(now.day());
    Serial.write('/');
    Serial.print(now.month()); 
    Serial.write('/');
    Serial.print(now.year(), DEC);
    Serial.println();

    return;
}
bool getTime(const char *str)
{
  int Hour, Min, Sec;

  if (sscanf(str, "%d:%d:%d", &Hour, &Min, &Sec) != 3) return false;
  tm.Hour = Hour;
  tm.Minute = Min;
  tm.Second = Sec;
  return true;
}

bool getDate(const char *str)
{
  char Month[12];
  int Day, Year;
  uint8_t monthIndex;

  if (sscanf(str, "%s %d %d", Month, &Day, &Year) != 3) return false;
  for (monthIndex = 0; monthIndex < 12; monthIndex++) {
    if (strcmp(Month, monthName[monthIndex]) == 0) break;
  }
  if (monthIndex >= 12) return false;
  tm.Day = Day;
  tm.Month = monthIndex + 1;
  tm.Year = CalendarYrToTm(Year);
  return true;
}

void print2digits(int number) {
  if (number >= 0 && number < 10) {
    Serial.write('0');
  }
  Serial.print(number);
}
