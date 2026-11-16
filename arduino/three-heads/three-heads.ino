#include <Stepper.h>

Stepper leftHead(2048, 8, 10, 9, 11);
Stepper upHead(2048, 4, 6, 5, 7);
Stepper rightHead(2048, 17, 15, 16, 14);

int foxCode = -1;

void setup() {
  delay(3000);

  Serial.begin(9600);
}

void loop() {
  while (Serial.available()) {
    foxCode = Serial.read();
  }

  switch (foxCode) {
    case 2:

      moveHead(1, -900);
      delay(200);
      moveHead(1, 900);
      waitOrStop(3000);
      break;

    case 3:

      moveHead(2, 4800);
      delay(200);
      moveHead(2, -4800);
      waitOrStop(3000);
      break;

    case 4:

      moveHead(3, -900);
      delay(200);
      moveHead(3, 900);
      waitOrStop(3000);
      break;

    case 5:

      moveHead(1, -900);
      waitForMessage();  // hold: stay out until wekinator says something different
      moveHead(1, 900);
      waitOrStop(1000);
      break;

    case 6:

      moveHead(2, 5000);
      waitForMessage();  // hold: stay out until wekinator says something different
      moveHead(2, -5000);
      waitOrStop(1000);
      break;

    case 7:

      moveHead(3, -900);
      waitForMessage();  // hold: stay out until wekinator says something different
      moveHead(3, 900);
      waitOrStop(1000);
      break;
  }

  foxCode = -1;
}

// wait until a new message arrives, however long that takes.
void waitForMessage() {
  while (Serial.available() == 0) {
    delay(100);
  }
}

void waitOrStop(int milliseconds) {
  for (int i = 0; i < milliseconds / 100; i++) {
    if (Serial.available()) {
      break;
    }
    delay(100);
  }
}

void moveHead(int head, int steps) {
  int direction = 1;
  if (steps < 0) {
    direction = -1;
  }

  int total = abs(steps);

  for (int i = 0; i < total; i++) {
    int speed = 14;
    if (head == 2) {
      speed = 12;
    }

    if (i < 100 || i >= total - 100) {
      speed = 4;
    }

    if (head == 1) {
      leftHead.setSpeed(speed);
      leftHead.step(direction);
    }
    if (head == 2) {
      upHead.setSpeed(speed);
      upHead.step(direction);
    }
    if (head == 3) {
      rightHead.setSpeed(speed);
      rightHead.step(direction);
    }
  }
}
