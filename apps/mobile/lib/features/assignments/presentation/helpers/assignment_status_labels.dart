import 'package:mobile_domain/src/assignment_status.dart';

/// Spanish labels for assignment board statuses.
String assignmentStatusLabel(AssignmentStatus? status) {
  return switch (status) {
    AssignmentStatus.draft => 'Borrador',
    AssignmentStatus.confirmed => 'Confirmado',
    AssignmentStatus.final_ => 'Finalizado',
    AssignmentStatus.replaced => 'Reemplazado',
    AssignmentStatus.cancelled => 'Cancelado',
    null => 'Sin estado',
  };
}
