import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/assignments/presentation/widgets/board_block_reason.dart';

void main() {
  group('displayBoardBlockReason', () {
    test('oculta motivos redundantes', () {
      expect(displayBoardBlockReason('Ya asignado a esta reserva'), isNull);
      expect(
        displayBoardBlockReason('Ya asignado a otra reserva en la misma fecha'),
        isNull,
      );
      expect(displayBoardBlockReason('Ya asignada a esta reserva'), isNull);
      expect(displayBoardBlockReason('Silla eliminada'), isNull);
      expect(displayBoardBlockReason('Equino no disponible'), isNull);
      expect(displayBoardBlockReason('Silla no disponible'), isNull);
      expect(displayBoardBlockReason('Equino inactivo'), isNull);
    });

    test('muestra motivos con detalle útil', () {
      expect(displayBoardBlockReason('En descanso'), 'En descanso');
      expect(displayBoardBlockReason('En mantenimiento'), 'En mantenimiento');
      expect(
        displayBoardBlockReason('Estado operativo: injured'),
        'Estado operativo: Lesionado',
      );
      expect(
        displayBoardBlockReason('Estado operativo: resting'),
        'Estado operativo: Descanso',
      );
    });
  });
}
