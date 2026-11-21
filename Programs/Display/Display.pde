import java.io.File;
import java.lang.Math;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.apache.commons.io.FilenameUtils;

File root;
File[] bodyPaths;
double simTime = 0d;

// TODO: Figure out how to implement `record` in Processing
class Frame {
  double time;
  Vec3D position;
  Vec3D velocity;

  Frame(double time, Vec3D position, Vec3D velocity) {
    this.time = time;
    this.position = position;
    this.velocity = velocity;
  }
}
Map<String, Frame[]> ephemerides = new HashMap<>();
Frame getTime(Frame[] ephemeride, double t) {
  if (t <= ephemeride[0].time) return ephemeride[0];
  if (t >= ephemeride[ephemeride.length - 1].time) return ephemeride[ephemeride.length - 1];
  int low = 0;
  int high = ephemeride.length - 1;
  // Binary search for the time
  while (low <= high) {
    int mid = low + (high - low) / 2;
    Frame frame = ephemeride[mid];
    // If we find the exact time, return it
    if (frame.time == t) {
      return frame;
    }
    if (frame.time < t) low = mid + 1;
    else high = mid - 1;
  }

  // Linearly interpolate between high and low
  Frame before = ephemeride[high];
  Frame after = ephemeride[low];
  double fraction = (t - before.time) / (after.time - before.time);
  Vec3D position = before.position.add(after.position.sub(before.position).mul(fraction));
  Vec3D velocity = before.velocity.add(after.velocity.sub(before.velocity).mul(fraction));
  return new Frame(t, position, velocity);
}

// Non-data lines in our given file
boolean ephemerisPass(String str) {
  boolean isEmpty = str.isEmpty();
  boolean isComment = str.startsWith("//");
  int numFloats = 7;
  // Match exactly numFloats numbers separated by spaces
  String floatPattern = "-?\\d+(\\.\\d*)?([eE][+-]?\\d+)?";
  boolean floatStream = str.matches("^" + floatPattern + "( +" + floatPattern + "){" + (numFloats - 1) + "}$");
  return !(isEmpty || isComment) && floatStream;
}

void setup() {
  size(800, 500);
  background(73, 146, 186);
  // Suppress a warning for high-density screens
  pixelDensity(2);
  // Get the root of the project
  root = new File(sketchPath()).getParentFile().getParentFile();
  // Get all text files in the folder
  bodyPaths = new File(root, "Fitted Orbits").listFiles(file -> file.getName().endsWith(".txt"));
  for (File bodyPath : bodyPaths) {
    String name = FilenameUtils.removeExtension(bodyPath.getName());
    // Grab all lines in the file that are determined to be valid (return 'true' in ephemerisPass()) //<>//
    try (Stream<String> sstream = Files.lines(bodyPath.toPath()).filter(line -> ephemerisPass(line.trim()))) {
      // Collect everything and add it to the ephemeris
      List<String> lines = sstream.collect(Collectors.toList());
      Frame[] frames = new Frame[lines.size()];
      println("Body " + name + " has length " + lines.size());
      for (int i = 0; i < lines.size(); i++) {
        String line = lines.get(i);
        String[] numberStrs = line.split(" ");
        double[] numbers = Arrays.stream(numberStrs).mapToDouble(Double::parseDouble).toArray();
        // Since the line passed ephemerisPass, we know this line is safe
        frames[i] = new Frame(numbers[0], new Vec3D(numbers[1], numbers[2], numbers[3]), new Vec3D(numbers[4], numbers[5], numbers[6]));
      }
      ephemerides.put(name,frames);
    } catch (IOException e) {
      e.printStackTrace();
      exit();
    }
  }
}

void draw() {
  background(73, 146, 186);
  Vec2D center = new Vec2D(width / 2, height / 2);
  simTime += 60 * 60 * 24;
  simTime %= 31536000d;
  double scale = 275;
  fill(120, 29, 58);
  for (String name : ephemerides.keySet()) {
    Frame simFrame = getTime(ephemerides.get(name), simTime);
    Vec3D position = simFrame.position.div(149597870700d); // Divide by an AU
    Vec2D drawPosition = position.flatten().mul(scale).add(center);
    circle((float)drawPosition.x, (float)drawPosition.y, 25);
  }
}
