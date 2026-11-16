#include <Stepper.h>

Stepper upHead(2048, 4, 6, 5, 7);
Stepper leftHead(2048, 8, 10, 9, 11);
Stepper rightHead(2048, 17, 15, 16, 14);

void setup() {

  delay(3000);

  leftHead.setSpeed(12);
  upHead.setSpeed(10);
  rightHead.setSpeed(12);
}

void loop() {

  moveHead(1, -900);
  delay(200);
  moveHead(1, 900);
  delay(1000);

  moveHead(2, 4800);
  delay(200);
  moveHead(2, -4800);
  delay(1000);

  moveHead(3, -900);
  delay(200);
  moveHead(3, 900);
  delay(1000);

  moveHead(1, -900);
  delay(3000);
  moveHead(1, 900);
  delay(1000);

  moveHead(2, 5000);
  delay(3000);
  moveHead(2, -5000);
  delay(1000);

  moveHead(3, -900);
  delay(3000);
  moveHead(3, 900);
  delay(1000);
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
