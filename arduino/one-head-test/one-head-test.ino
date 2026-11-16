#include <Stepper.h>

Stepper head(2048, 8, 10, 9, 11);

void setup() {
  delay(3000);

  head.setSpeed(10);
}

void loop() {
  head.step(900);
  delay(1000);
  head.step(-900);
  delay(1000);
}
