import 'package:mobile_domain/src/equines/equine_operational_status.dart';

/// Tipos de evento de equino → etiqueta UI.
const equineEventTypeOptions = <String, String>{
  'health_check': 'Control de salud',
  'injury': 'Lesión',
  'treatment': 'Tratamiento',
  'medication': 'Medicación',
  'vaccination': 'Vacunación',
  'farrier': 'Herraje',
  'hoof_care': 'Cuidado de cascos',
  'dentistry': 'Odontología',
  'weight': 'Peso',
  'height': 'Altura',
  'training': 'Entrenamiento',
  'nutrition': 'Nutrición',
  'lab_test': 'Laboratorio',
  'rest': 'Descanso',
  'availability_change': 'Cambio de disponibilidad',
  'route_activity': 'Actividad en ruta',
  'note': 'Nota de manejo',
};

String equineEventTypeLabel(String type) =>
    equineEventTypeOptions[type] ?? 'Otro evento';

const equineEventSeverityOptions = <String, String>{
  'low': 'Baja',
  'medium': 'Media',
  'high': 'Alta',
  'critical': 'Crítica',
};

String equineEventSeverityLabel(String severity) =>
    equineEventSeverityOptions[severity] ?? 'Sin severidad';

String equineOperationalStatusApiValue(EquineOperationalStatus status) {
  switch (status) {
    case EquineOperationalStatus.available:
      return 'available';
    case EquineOperationalStatus.resting:
      return 'resting';
    case EquineOperationalStatus.inService:
      return 'in_service';
    case EquineOperationalStatus.injured:
      return 'injured';
    case EquineOperationalStatus.retired:
      return 'retired';
    case EquineOperationalStatus.unavailable:
      return 'unavailable';
    case EquineOperationalStatus.restricted:
      return 'restricted';
  }
}

bool equineEventShowsWeightField(String eventType) => eventType == 'weight';

bool equineEventShowsNextDueField(String eventType) =>
    eventType == 'vaccination' ||
    eventType == 'medication' ||
    eventType == 'treatment';

bool equineEventShowsAvailabilityFields(String eventType) =>
    eventType == 'injury' ||
    eventType == 'treatment' ||
    eventType == 'rest' ||
    eventType == 'availability_change';
