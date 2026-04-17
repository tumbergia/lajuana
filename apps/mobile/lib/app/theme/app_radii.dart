import 'package:flutter/material.dart';

abstract final class AppRadii {
  static const Radius defaultRadius = Radius.circular(2);
  static const Radius lg = Radius.circular(4);
  static const Radius xl = Radius.circular(8);
  static const Radius full = Radius.circular(12);

  static const BorderRadius radiusDefault = BorderRadius.all(defaultRadius);
  static const BorderRadius radiusLg = BorderRadius.all(lg);
  static const BorderRadius radiusXl = BorderRadius.all(xl);
  static const BorderRadius radiusFull = BorderRadius.all(full);
}
