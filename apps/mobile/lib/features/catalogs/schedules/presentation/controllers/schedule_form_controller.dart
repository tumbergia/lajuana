import 'package:flutter/foundation.dart';

import '../../domain/schedule_status.dart';

class ScheduleFormController extends ChangeNotifier {
  String experienceId = '';
  String dateIso = '';
  String startTime = '08:00:00';
  bool isActive = true;
  int capacityTotal = 1;
  int reservedSlots = 0;
  int internalSlots = 0;
  int blockedSlots = 0;
  bool customRequestOnly = false;
  String notes = '';
  CatalogScheduleStatus status = CatalogScheduleStatus.open;

  int get availableSlots =>
      capacityTotal - reservedSlots - internalSlots - blockedSlots;

  String? validate() {
    if (experienceId.trim().isEmpty) {
      return 'Debes seleccionar una experiencia.';
    }
    if (dateIso.trim().isEmpty) {
      return 'La fecha es obligatoria.';
    }
    if (capacityTotal <= 0) {
      return 'La capacidad total debe ser mayor a 0.';
    }
    if (reservedSlots < 0 || internalSlots < 0 || blockedSlots < 0) {
      return 'Los cupos no pueden ser negativos.';
    }
    if (reservedSlots > capacityTotal ||
        internalSlots > capacityTotal ||
        blockedSlots > capacityTotal) {
      return 'Ningun cupo puede superar la capacidad total.';
    }
    if (availableSlots < 0) {
      return 'La combinacion de cupos deja disponibilidad negativa.';
    }
    return null;
  }
}
