import 'package:flutter/foundation.dart';

import '../../domain/models/reservation_detail.dart';
import '../../domain/models/reservation_participant_detail.dart';

/// Estado de la subruta Participantes dentro del detalle de reserva.
///
/// Recibe datos desde [ReservationDetailController] — no hace fetch independiente.
class ReservationParticipantsSectionController extends ChangeNotifier {
  List<ReservationParticipantDetail> participants = const [];
  int totalExpected = 0;
  int totalCompleted = 0;
  bool hasMedicalAlert = false;
  bool hasFoodRestriction = false;

  /// Actualiza el estado desde el detalle de la reserva.
  void updateFromDetail(ReservationDetail detail) {
    participants = detail.participants;
    totalExpected =
        detail.expectedParticipantsCount ?? detail.participantCount;
    totalCompleted = detail.participantsCompletedCount;
    hasMedicalAlert = participants.any((p) => p.hasMedicalAlert);
    hasFoodRestriction = participants.any((p) => p.hasFoodRestriction);
    notifyListeners();
  }

  void reset() {
    participants = const [];
    totalExpected = 0;
    totalCompleted = 0;
    hasMedicalAlert = false;
    hasFoodRestriction = false;
    notifyListeners();
  }
}
