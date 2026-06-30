import 'package:mobile_ui/src/widgets/app_badge.dart';

class ReservationRecord {
  const ReservationRecord({
    required this.code,
    required this.clientName,
    required this.equineName,
    required this.slotLabel,
    required this.status,
    required this.hasPendingSync,
    required this.hasSyncError,
    this.id,
    this.statusRaw,
    this.experienceName,
    this.participantCount,
    this.registeredCount,
    this.paymentStatus,
    this.formStatus,
    this.requestedDate,
    this.isDeleted = false,
  });

  final String code;
  final String clientName;
  final String equineName;
  final String slotLabel;
  final String status;
  final bool hasPendingSync;
  final bool hasSyncError;

  // New fields for real data
  final String? id;
  final dynamic statusRaw; // ReservationStatus or String
  final String? experienceName;
  final int? participantCount;
  final int? registeredCount;
  final String? paymentStatus;
  final String? formStatus;
  final String? requestedDate;
  final bool isDeleted;
}

class ReservationParticipantRecord {
  const ReservationParticipantRecord({
    required this.reservationCode,
    required this.fullName,
    required this.completionLabel,
    required this.isComplete,
  });

  final String reservationCode;
  final String fullName;
  final String completionLabel;
  final bool isComplete;
}

class ReservationPaymentProofRecord {
  const ReservationPaymentProofRecord({
    required this.reservationCode,
    required this.proofCode,
    required this.statusLabel,
    required this.statusTone,
  });

  final String reservationCode;
  final String proofCode;
  final String statusLabel;
  final AppBadgeTone statusTone;
}

class ReservationAssignmentRecord {
  const ReservationAssignmentRecord({
    required this.reservationCode,
    required this.rider,
    required this.equine,
    required this.statusLabel,
    required this.statusTone,
  });

  final String reservationCode;
  final String rider;
  final String equine;
  final String statusLabel;
  final AppBadgeTone statusTone;
}

class ReservationPresentationFixtures {
  const ReservationPresentationFixtures._();

  static const List<ReservationRecord> reservations = <ReservationRecord>[
    ReservationRecord(
      code: 'RV-1042',
      clientName: 'Elena Rodriguez',
      equineName: 'Cosaco 24',
      slotLabel: '24 Oct 2026 - 09:00',
      status: 'pendientes',
      hasPendingSync: true,
      hasSyncError: false,
    ),
    ReservationRecord(
      code: 'RV-1039',
      clientName: 'Marcus Thorne',
      equineName: 'Amanecer',
      slotLabel: '24 Oct 2026 - 11:30',
      status: 'confirmadas',
      hasPendingSync: false,
      hasSyncError: false,
    ),
    ReservationRecord(
      code: 'RV-1032',
      clientName: 'Carla Mejia',
      equineName: 'Granito',
      slotLabel: '23 Oct 2026 - 16:00',
      status: 'finalizadas',
      hasPendingSync: false,
      hasSyncError: false,
    ),
    ReservationRecord(
      code: 'RV-1029',
      clientName: 'Santiago Velez',
      equineName: 'Ronda',
      slotLabel: '23 Oct 2026 - 09:30',
      status: 'pendientes',
      hasPendingSync: true,
      hasSyncError: false,
    ),
    ReservationRecord(
      code: 'RV-1022',
      clientName: 'Paola Diaz',
      equineName: 'Marte',
      slotLabel: '22 Oct 2026 - 15:45',
      status: 'confirmadas',
      hasPendingSync: false,
      hasSyncError: true,
    ),
    ReservationRecord(
      code: 'RV-1018',
      clientName: 'Luis Herrera',
      equineName: 'Candelaria',
      slotLabel: '22 Oct 2026 - 08:10',
      status: 'pendientes',
      hasPendingSync: true,
      hasSyncError: false,
    ),
    ReservationRecord(
      code: 'RV-1011',
      clientName: 'Diana Suarez',
      equineName: 'Pradera',
      slotLabel: '21 Oct 2026 - 10:00',
      status: 'finalizadas',
      hasPendingSync: false,
      hasSyncError: false,
    ),
  ];

  static const List<ReservationParticipantRecord> participants =
      <ReservationParticipantRecord>[
        ReservationParticipantRecord(
          reservationCode: 'RV-1042',
          fullName: 'Elena Rodriguez',
          completionLabel: '100%',
          isComplete: true,
        ),
        ReservationParticipantRecord(
          reservationCode: 'RV-1039',
          fullName: 'Marcus Thorne',
          completionLabel: '80%',
          isComplete: false,
        ),
        ReservationParticipantRecord(
          reservationCode: 'RV-1029',
          fullName: 'Santiago Velez',
          completionLabel: '60%',
          isComplete: false,
        ),
      ];

  static const List<ReservationPaymentProofRecord> paymentProofs =
      <ReservationPaymentProofRecord>[
        ReservationPaymentProofRecord(
          reservationCode: 'RV-1042',
          proofCode: 'PAY-512',
          statusLabel: 'Pendiente de sync',
          statusTone: AppBadgeTone.warning,
        ),
        ReservationPaymentProofRecord(
          reservationCode: 'RV-1039',
          proofCode: 'PAY-508',
          statusLabel: 'Sincronizado',
          statusTone: AppBadgeTone.success,
        ),
        ReservationPaymentProofRecord(
          reservationCode: 'RV-1022',
          proofCode: 'PAY-497',
          statusLabel: 'Fallo de carga',
          statusTone: AppBadgeTone.danger,
        ),
      ];

  static const List<ReservationAssignmentRecord> assignments =
      <ReservationAssignmentRecord>[
        ReservationAssignmentRecord(
          reservationCode: 'RV-1042',
          rider: 'Andrea Mesa',
          equine: 'Cosaco 24',
          statusLabel: 'Preliminar',
          statusTone: AppBadgeTone.warning,
        ),
        ReservationAssignmentRecord(
          reservationCode: 'RV-1039',
          rider: 'Equipo A',
          equine: 'Amanecer',
          statusLabel: 'Consolidado',
          statusTone: AppBadgeTone.success,
        ),
      ];
}
