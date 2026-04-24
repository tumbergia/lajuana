import 'package:flutter/foundation.dart';

class ExperienceFormController extends ChangeNotifier {
  String name = '';
  String slug = '';
  String description = '';
  String level = 'basic';
  int? durationHours;
  int? durationDays;
  int? baseCapacity;
  bool isActive = true;

  String? validate() {
    if (name.trim().isEmpty) return 'El nombre es obligatorio.';
    if (slug.trim().isEmpty) return 'El slug es obligatorio.';
    if ((durationHours == null || durationHours! <= 0) &&
        (durationDays == null || durationDays! <= 0)) {
      return 'Debes ingresar duracion en horas o dias.';
    }
    return null;
  }

  void updateName(String value) {
    name = value;
    if (slug.trim().isEmpty) {
      slug = _slugify(value);
    }
    notifyListeners();
  }

  void updateSlug(String value) {
    slug = value.trim();
    notifyListeners();
  }

  void updateDescription(String value) {
    description = value;
    notifyListeners();
  }

  void updateLevel(String value) {
    level = value;
    notifyListeners();
  }

  void updateDurationHours(int? value) {
    durationHours = value;
    notifyListeners();
  }

  void updateDurationDays(int? value) {
    durationDays = value;
    notifyListeners();
  }

  void updateBaseCapacity(int? value) {
    baseCapacity = value;
    notifyListeners();
  }

  void updateIsActive(bool value) {
    isActive = value;
    notifyListeners();
  }

  String _slugify(String value) {
    final lowered = value.toLowerCase().trim();
    final normalized = lowered
        .replaceAll(RegExp(r'[^a-z0-9\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '-')
        .replaceAll(RegExp(r'-+'), '-');
    return normalized;
  }
}
