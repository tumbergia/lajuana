import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/assignments/presentation/helpers/assignment_status_labels.dart';
import 'package:mobile_domain/src/assignment_status.dart';

void main() {
  test('maps all assignment statuses to Spanish', () {
    expect(assignmentStatusLabel(AssignmentStatus.draft), 'Borrador');
    expect(assignmentStatusLabel(AssignmentStatus.confirmed), 'Confirmado');
    expect(assignmentStatusLabel(AssignmentStatus.final_), 'Finalizado');
    expect(assignmentStatusLabel(AssignmentStatus.replaced), 'Reemplazado');
    expect(assignmentStatusLabel(AssignmentStatus.cancelled), 'Cancelado');
    expect(assignmentStatusLabel(null), 'Sin estado');
  });
}
