import java.io.File;
import java.lang.Math;

File root;
File[] bodyPaths;
double time = 0d;

void setup() {
  size(800, 500);
  background(73, 146, 186);
  // Suppress a warning for high-density screens
  pixelDensity(2);
  // Get the root of the project
  root = new File(sketchPath()).getParentFile().getParentFile();
  // I want to use prints sparingly, but as this project is just getting off the ground I'm fine with debug prints
  println("The root is " + root.getAbsolutePath());
  // Get all text files in the folder. Not yet used
  bodyPaths = root.listFiles(file -> file.getName().endsWith(".txt"));
}

void draw() {
  background(73, 146, 186);
  // Movement! Trying to relearn a language I used probably four-ish years ago is hard...
  Vec2D position = new Vec2D(Math.cos(time), Math.sin(time)).mul(150);
  time += 0.01;
  Vec2D center = new Vec2D(width / 2, height / 2).add(position);
  fill(120, 29, 58);
  ellipse((float)center.x, (float)center.y, 100, 100);
  fill(179, 43, 86);
  textSize(200);
  text("Hello,", 90, 220);
  text("World", 300, 370);
}