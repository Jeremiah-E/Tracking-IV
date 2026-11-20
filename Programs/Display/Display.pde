// Like the C++ program, this is mostly here for organizational purposes
// It's effectively a hello, world program right now

void setup() {
  size(800, 500);
  background(73, 146, 186);
  // Suppress a warning for high-density screens
  pixelDensity(2);
}

void draw() {
  background(73, 146, 186);
  fill(179, 43, 86);
  textSize(200);
  text("Hello,", 90, 220);
  text("World", 300, 370);
}
