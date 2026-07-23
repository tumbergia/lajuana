import 'package:mobile_domain/src/equines/equine_experience_fit.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';

/// Human-readable labels for equine enums and backend codes.
/// Single source of truth — never expose raw enum values to the user.

/// Species codes → display name.
String equineSpeciesLabel(String species) {
  switch (species) {
    case 'mule':
      return 'Mula';
    case 'donkey':
      return 'Asno';
    case 'horse':
      return 'Caballo';
    default:
      return 'Otra especie';
  }
}

/// Gender/sex codes → display name.
String equineSexLabel(String sex) {
  switch (sex) {
    case 'male':
      return 'Macho';
    case 'female':
      return 'Hembra';
    default:
      return 'Sin dato';
  }
}

/// Location status codes → display name.
String equineLocationLabel(String location) {
  switch (location) {
    case 'la_juana':
      return 'La Juana';
    case 'other':
      return 'Otras instalaciones';
    default:
      return 'Ubicación desconocida';
  }
}

/// Operational status enum → display name.
String equineStatusLabel(EquineOperationalStatus status) {
  switch (status) {
    case EquineOperationalStatus.available:
      return 'Disponible';
    case EquineOperationalStatus.resting:
      return 'Descanso';
    case EquineOperationalStatus.inService:
      return 'En servicio';
    case EquineOperationalStatus.injured:
      return 'Lesionado';
    case EquineOperationalStatus.retired:
      return 'Retirado';
    case EquineOperationalStatus.unavailable:
      return 'No disponible';
    case EquineOperationalStatus.restricted:
      return 'Restringido';
  }
}

/// Experience fit enum → display name.
String equineExperienceLabel(EquineExperienceFit? fit) {
  if (fit == null) return '';
  switch (fit) {
    case EquineExperienceFit.beginner:
      return 'Principiante';
    case EquineExperienceFit.intermediate:
      return 'Intermedio';
    case EquineExperienceFit.advanced:
      return 'Avanzado';
    case EquineExperienceFit.all:
      return 'Todos los niveles';
    case EquineExperienceFit.staffOnly:
      return 'Solo personal';
    case EquineExperienceFit.notAssignable:
      return 'No asignable';
  }
}

/// Availability boolean → display name.
String equineAvailabilityLabel(bool available) =>
    available ? 'Disponible' : 'No disponible';

/// Active boolean → display name.
String equineActiveLabel(bool active) => active ? 'Activo' : 'Inactivo';

/// Yes/No helper.
String equineYesNo(bool value) => value ? 'Sí' : 'No';

/// Weight formatting.
String equineWeightLabel(double? kg) =>
    kg != null ? '${kg.toStringAsFixed(0)} kg' : '';

/// Height formatting.
String equineHeightLabel(double? m) =>
    m != null ? '${m.toStringAsFixed(2)} m' : '';

// ── Field / section labels for the equine profile card ─────────────────

/// "Edad" field.
String equineAgeLabel() => 'Edad';

/// "años aprox." suffix.
String equineYearsLabel() => 'años aprox.';

/// "Peso" field title.
String equineWeightLabelTitle() => 'Peso';

/// "Carga máx." field title.
String equineMaxLoadLabel() => 'Carga máx.';

/// "Estado" section header.
String equineStatusSectionLabel() => 'Estado';

/// "Estado" field label.
String equineStatusFieldLabel() => 'Estado';

/// "Ubicación" field label.
String equineLocationFieldLabel() => 'Ubicación';

/// "Experiencia" field label.
String equineExperienceFieldLabel() => 'Experiencia';

/// "Actividad" section header.
String equineActivitySectionLabel() => 'Actividad';

/// "Último servicio" field label.
String equineLastServiceLabel() => 'Último servicio';

/// "Carga semanal" field label.
String equineWeeklyLoadLabel() => 'Carga semanal';

/// Formatted service count, e.g. "4 servicios".
String equineServiceCountLabel(int count) => '$count servicios';
