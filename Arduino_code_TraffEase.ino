// Pin Definitions
const int NS_SG = 2, NS_RG = 3, NS_Y = 4, NS_R = 5;
const int EW_SG = 6, EW_RG = 7, EW_Y = 8, EW_R = 9;

String emergencyDirection = "";
bool emergencyDetected = false;

// Car counts received from Python
int countN = 0, countS = 0, countE = 0, countW = 0;

void setup() {
  Serial.begin(9600);
  for (int pin = 2; pin <= 9; pin++) pinMode(pin, OUTPUT);
}

// Function to inform Python which side is green
void sendLightStatus(String active) {
  Serial.println("ACTIVE:" + active); 
}

void allRed() {
  digitalWrite(NS_R, HIGH);
  digitalWrite(EW_R, HIGH);
  digitalWrite(NS_SG, LOW);
  digitalWrite(NS_RG, LOW);
  digitalWrite(NS_Y, LOW);
  digitalWrite(EW_SG, LOW);
  digitalWrite(EW_RG, LOW);
  digitalWrite(EW_Y, LOW);
  delay(2000); // all red buffer
}

int dynamicTime(int count) {
  return constrain(5000 + count * 1000, 5000, 20000);
}

int dynamicRightTime(int count) {
  return constrain(4000 + count * 500, 4000, 10000);
}

void handleEmergency() {
  if (emergencyDetected) {
    Serial.println("EMERGENCY: " + emergencyDirection);

    if (emergencyDirection == "N" || emergencyDirection == "S") {
      NS_Straight_Phase();
    } else if (emergencyDirection == "E" || emergencyDirection == "W") {
      EW_Straight_Phase();
    }

    delay(15000);
    allRed();
    emergencyDetected = false;
    emergencyDirection = "";
  }
}

void NS_Straight_Phase() {
  sendLightStatus("NS");
  digitalWrite(NS_R, LOW);
  digitalWrite(EW_R, HIGH);
  digitalWrite(NS_SG, HIGH);

  int greenTime = dynamicTime(countN + countS);
  delay(greenTime);

  digitalWrite(NS_SG, LOW);
  digitalWrite(NS_Y, HIGH);
  delay(3000);
  digitalWrite(NS_Y, LOW);
  digitalWrite(NS_R, HIGH);
  allRed();
}

void NS_RightTurn_Phase() {
  digitalWrite(NS_RG, HIGH);
  int rightTime = dynamicRightTime(countN + countS);
  delay(rightTime);
  digitalWrite(NS_RG, LOW);
  allRed();
}

void EW_Straight_Phase() {
  sendLightStatus("EW");
  digitalWrite(EW_R, LOW);
  digitalWrite(NS_R, HIGH);
  digitalWrite(EW_SG, HIGH);

  int greenTime = dynamicTime(countE + countW);
  delay(greenTime);

  digitalWrite(EW_SG, LOW);
  digitalWrite(EW_Y, HIGH);
  delay(3000);
  digitalWrite(EW_Y, LOW);
  digitalWrite(EW_R, HIGH);
  allRed();
}

void EW_RightTurn_Phase() {
  digitalWrite(EW_RG, HIGH);
  int rightTime = dynamicRightTime(countE + countW);
  delay(rightTime);
  digitalWrite(EW_RG, LOW);
  allRed();
}

// Receive counts from Python
void readCounts() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.startsWith("EMG:")) {
      emergencyDirection = input.substring(4);
      emergencyDetected = true;
      return;
    }

    int n = input.indexOf("N:");
    int s = input.indexOf("S:");
    int e = input.indexOf("E:");
    int w = input.indexOf("W:");

    if (n != -1 && s != -1) countN = input.substring(n + 2, s).toInt();
    if (s != -1 && e != -1) countS = input.substring(s + 2, e).toInt();
    if (e != -1 && w != -1) countE = input.substring(e + 2, w).toInt();
    if (w != -1) countW = input.substring(w + 2).toInt();
  }
}

void loop() {
  readCounts();        // get updated car counts
  handleEmergency();   // handle ambulance

  NS_Straight_Phase();
  NS_RightTurn_Phase();
  EW_Straight_Phase();
  EW_RightTurn_Phase();
}

