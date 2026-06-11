import 'package:flutter/foundation.dart';
import 'package:mobile_domain/src/equines/equine_event.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile/features/equines/presentation/equine_event_labels.dart';

enum EquineEventSaveState { idle, saving, success, error }

class EquineEventsController extends ChangeNotifier {
  EquineEventsController({required EquineEventRepository repository})
      : _repository = repository;

  final EquineEventRepository _repository;

  String eventType = 'note';
  DateTime happenedAt = DateTime.now();
  String title = '';
  String description = '';
  String? severity;
  bool affectsAvailability = false;
  EquineOperationalStatus resultingOperationalStatus =
      EquineOperationalStatus.injured;
  DateTime? restUntil;
  String measuredWeightText = '';
  DateTime? nextDueAt;
  String performedBy = '';

  EquineEventSaveState saveState = EquineEventSaveState.idle;
  String? validationError;
  String? saveError;
  EquineEvent? lastCreated;

  bool get showWeightField => equineEventShowsWeightField(eventType);
  bool get showNextDueField => equineEventShowsNextDueField(eventType);
  bool get showAvailabilityFields =>
      equineEventShowsAvailabilityFields(eventType);

  void setEventType(String value) {
    eventType = value;
    if (!equineEventShowsAvailabilityFields(value)) {
      affectsAvailability = false;
    } else if (value == 'injury' || value == 'rest') {
      affectsAvailability = true;
    }
    if (value == 'rest') {
      resultingOperationalStatus = EquineOperationalStatus.resting;
    } else if (value == 'injury') {
      resultingOperationalStatus = EquineOperationalStatus.injured;
    } else if (value == 'treatment') {
      resultingOperationalStatus = EquineOperationalStatus.restricted;
    }
    notifyListeners();
  }

  void setHappenedAt(DateTime value) {
    happenedAt = value;
    notifyListeners();
  }

  void setTitle(String value) {
    title = value;
    notifyListeners();
  }

  void setDescription(String value) {
    description = value;
    notifyListeners();
  }

  void setSeverity(String? value) {
    severity = value;
    notifyListeners();
  }

  void setAffectsAvailability(bool value) {
    affectsAvailability = value;
    notifyListeners();
  }

  void setResultingOperationalStatus(EquineOperationalStatus value) {
    resultingOperationalStatus = value;
    notifyListeners();
  }

  void setRestUntil(DateTime? value) {
    restUntil = value;
    notifyListeners();
  }

  void setMeasuredWeightText(String value) {
    measuredWeightText = value;
    notifyListeners();
  }

  void setNextDueAt(DateTime? value) {
    nextDueAt = value;
    notifyListeners();
  }

  void setPerformedBy(String value) {
    performedBy = value;
    notifyListeners();
  }

  String? validate() {
    final trimmedTitle = title.trim();
    if (trimmedTitle.isEmpty) {
      return 'El título es obligatorio.';
    }

    if (showWeightField) {
      final weight = double.tryParse(measuredWeightText.replaceAll(',', '.'));
      if (weight == null || weight <= 0) {
        return 'Ingresá un peso válido en kg.';
      }
    }

    if (affectsAvailability) {
      if (description.trim().isEmpty) {
        return 'Indicá el motivo cuando afecta la disponibilidad.';
      }
      if (restUntil == null &&
          resultingOperationalStatus == EquineOperationalStatus.available) {
        return 'Definí descanso hasta o un estado operativo distinto de disponible.';
      }
      if (eventType == 'rest' && restUntil == null) {
        return 'Indicá hasta cuándo dura el descanso.';
      }
    }

    return null;
  }

  Future<EquineEvent?> submit(String equineId) async {
    validationError = validate();
    if (validationError != null) {
      notifyListeners();
      return null;
    }

    saveState = EquineEventSaveState.saving;
    saveError = null;
    notifyListeners();

    try {
      final payload = EquineEventCreatePayload(
        eventType: eventType,
        happenedAt: happenedAt,
        title: title.trim(),
        description: description.trim().isEmpty ? null : description.trim(),
        severity: severity,
        measuredWeightKg: showWeightField
            ? double.tryParse(measuredWeightText.replaceAll(',', '.'))
            : null,
        nextDueAt: showNextDueField ? nextDueAt : null,
        performedBy: performedBy.trim().isEmpty ? null : performedBy.trim(),
        affectsAvailability: affectsAvailability,
        resultingOperationalStatus: affectsAvailability
            ? equineOperationalStatusApiValue(resultingOperationalStatus)
            : null,
        restUntil: affectsAvailability ? restUntil : null,
      );

      lastCreated = await _repository.createEvent(equineId, payload);
      saveState = EquineEventSaveState.success;
      notifyListeners();
      return lastCreated;
    } catch (e) {
      saveState = EquineEventSaveState.error;
      saveError = e.toString();
      notifyListeners();
      return null;
    }
  }
}
