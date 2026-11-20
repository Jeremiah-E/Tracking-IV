import java.lang.Math;

/*
 * A vector algebra library for 2D and 3D vectors
 * TODO: Include cross products, rotations, and transformations
 */

public class Vec3D {
  double x; double y; double z;
  public Vec3D(double x, double y, double z) {
    this.x = x;
    this.y = y;
    this.z = z;
  }
  public Vec3D(double[] v) {
    this(v[0], v[1], v[2]);
  }
  public Vec3D add(Vec3D other) {
    return new Vec3D(this.x + other.x, this.y + other.y, this.z + other.z);
  }
  public Vec3D sub(Vec3D other) {
    return new Vec3D(this.x - other.x, this.y - other.y, this.z - other.z);
  }
  public Vec3D mul(double scalar) {
    return new Vec3D(this.x * scalar, this.y * scalar, this.z * scalar);
  }
  public Vec3D mul(double scalar, Vec3D vec) {
    return vec.mul(scalar);
  }
  public Vec3D div(double scalar) {
    return new Vec3D(this.x / scalar, this.y / scalar, this.z / scalar);
  }
  public Vec3D div(double scalar, Vec3D vec) {
    return new Vec3D(scalar / vec.x, scalar / vec.y, scalar / vec.z);
  }
  public double dot(Vec3D vec) {
    return this.x * vec.x + this.y * vec.y + this.z * vec.z;
  }
  public double mag2() {
    return this.dot(this);
  }
  public double mag() {
    return Math.sqrt(this.mag2());
  }
}

public class Vec2D {
  double x; double y;
  public Vec2D(double x, double y) {
    this.x = x;
    this.y = y;
  }
  public Vec2D(double[] v) {
    this(v[0], v[1]);
  }
  public Vec2D add(Vec2D other) {
    return new Vec2D(this.x + other.x, this.y + other.y);
  }
  public Vec2D sub(Vec2D other) {
    return new Vec2D(this.x - other.x, this.y - other.y);
  }
  public Vec2D mul(double scalar) {
    return new Vec2D(this.x * scalar, this.y * scalar);
  }
  public Vec2D mul(double scalar, Vec2D vec) {
    return vec.mul(scalar);
  }
  public Vec2D div(double scalar) {
    return new Vec2D(this.x / scalar, this.y / scalar);
  }
  public Vec2D div(double scalar, Vec2D vec) {
    return new Vec2D(scalar / vec.x, scalar / vec.y);
  }
  public double dot(Vec2D vec) {
    return this.x * vec.x + this.y * vec.y;
  }
  public double mag2() {
    return this.dot(this);
  }
  public double mag() {
    return Math.sqrt(this.mag2());
  }
}