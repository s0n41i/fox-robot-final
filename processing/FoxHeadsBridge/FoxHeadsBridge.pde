import oscP5.*;
import processing.serial.*;

OscP5 oscP5;
Serial port;

// false = test without the arduino
boolean useArduino = true;

// wekinator's answers
int distance = 0;  // 1 close, 2 middle, 3 far
int hands = 0;     // 1 down, 2 hand out
int side = 0;      // 1 left, 2 middle, 3 right

// the last answers, to see if they changed
int lastDistance = 0;
int lastHands = 0;
int lastSide = 0;

// how many times in a row the answer was the same
int sameCount = 0;
int steady = 10;

// have we sent a move for this answer?
boolean sent = false;

int head = 0;           // 1 left, 2 up, 3 right
int foxClass = 0;       // 1 hide, 2-4 peek, 5-7 all out
int arduinoMessage = -1;

void setup() {
  size(400, 150);
  printArray(Serial.list());

  if (useArduino) {
    // find the arduino by name
    String[] ports = Serial.list();
    int portNumber = -1;
    for (int i = 0; i < ports.length; i++) {
      if (ports[i].indexOf("usbmodem") >= 0 || ports[i].indexOf("usbserial") >= 0) {
        portNumber = i;
      }
    }
    if (portNumber == -1) {
      println("no arduino found. plug it in, or set useArduino to false.");
      exit();
      return;
    }
    port = new Serial(this, ports[portNumber], 9600);
  }

  oscP5 = new OscP5(this, 12000);
}

void draw() {
  background(0);
  fill(255);
  textSize(16);
  showWhatWekinatorSaid();
  textSize(22);
  showWhatFoxDoes();
}

// runs when wekinator sends its answers
void oscEvent(OscMessage message) {
  if (message.checkAddrPattern("/wek/outputs") == false) {
    return;
  }
  distance = (int)message.get(0).floatValue();
  hands = (int)message.get(1).floatValue();
  side = (int)message.get(2).floatValue();

  // 1 and 2 were swapped in training. swap them back.
  if (side == 1) {
    side = 2;
  } else if (side == 2) {
    side = 1;
  }

  checkAnswer();
}

// only act when the answer is the same 10 times in a row
void checkAnswer() {
  if (distance == lastDistance && hands == lastHands && side == lastSide) {
    sameCount = sameCount + 1;
  } else {
    lastDistance = distance;
    lastHands = hands;
    lastSide = side;
    sameCount = 1;
    sent = false;
  }

  // (wait 5 seconds after start, the arduino restarts when the port opens)
  if (sameCount >= steady && sent == false && millis() > 5000) {
    chooseMove();
    sendToArduino();
    sent = true;
  }
}

// the further away you are, the longer the fox comes out
void chooseMove() {
  pickHead();
  if (distance == 1 && hands == 2) {
    // close, but your hand is out: the head on YOUR side comes out and holds.
    // (left side = left head = 1, middle = top head = 2, right side = right head = 3)
    head = side;
    foxClass = 4 + head;  // hold: 5, 6 or 7
  } else if (distance == 1) {
    // close: hide
    foxClass = 1;
  } else if (distance == 2) {
    // middle: peek
    foxClass = 1 + head;  // peek: 2, 3 or 4
  } else {
    // far: come out and hold
    foxClass = 4 + head;  // hold: 5, 6 or 7
  }
}

// pick the head on the other side from the visitor
void pickHead() {
  if (side == 1) {
    // you're on the left: the right head comes out
    head = 3;
  }
  if (side == 2) {
    // you're in the middle: the top head comes out
    head = 2;
  }
  if (side == 3) {
    // you're on the right: the left head comes out
    head = 1;
  }
}

void sendToArduino() {
  // don't send the same move twice in a row.
  // (so a head that is holding out doesn't go in and out again)
  if (foxClass == arduinoMessage) {
    return;
  }
  arduinoMessage = foxClass;
  println("sent to arduino: " + foxClass);
  if (useArduino) {
    port.write(foxClass);
  }
}

void showWhatWekinatorSaid() {
  if (distance == 1) {
    text("close,", 20, 40);
  }
  if (distance == 2) {
    text("middle,", 20, 40);
  }
  if (distance == 3) {
    text("far,", 20, 40);
  }

  if (hands == 2) {
    text("hand out,", 200, 40);
  }

  if (side == 1) {
    text("left", 110, 40);
  }
  if (side == 2) {
    text("middle", 110, 40);
  }
  if (side == 3) {
    text("right", 110, 40);
  }
}

void showWhatFoxDoes() {
  if (arduinoMessage == 1) {
    text("1: HIDES", 20, 90);
  } else if (arduinoMessage == 2) {
    text("2: left head peeks", 20, 90);
  } else if (arduinoMessage == 3) {
    text("3: up head peeks", 20, 90);
  } else if (arduinoMessage == 4) {
    text("4: right head peeks", 20, 90);
  } else if (arduinoMessage == 5) {
    text("5: left head holds out", 20, 90);
  } else if (arduinoMessage == 6) {
    text("6: up head holds out", 20, 90);
  } else if (arduinoMessage == 7) {
    text("7: right head holds out", 20, 90);
  } else {
    textSize(16);
    text("waiting for wekinator...", 20, 90);
  }
}
