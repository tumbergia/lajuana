/// La Juana Domain Layer.
///
/// Pure domain models, enums, and repository contracts shared across
/// mobile app packages.  No Flutter or infrastructure dependencies.
library mobile_domain;

export 'src/reservation_status.dart';
export 'src/assignment_status.dart';

// -- Extracted from apps/mobile (domain layer) --
export 'src/assignments/assignment.dart';
export 'src/assignments/assignment_board.dart';
export 'src/assignments/assignments_repository.dart';
export 'src/equines/equine.dart';
export 'src/equines/equine_experience_fit.dart';
export 'src/equines/equine_operational_status.dart';
export 'src/equines/equine_repository.dart';
export 'src/equines/equine_timeline_entry.dart';
export 'src/reservations/reservation_detail.dart';
export 'src/reservations/reservation_list_item.dart';
export 'src/reservations/reservation_operational_alert.dart';
export 'src/reservations/reservation_participant_detail.dart';
export 'src/reservations/reservation_payment_proof_detail.dart';
export 'src/reservations/reservation_payment_summary.dart';
export 'src/reservations/reservation_timeline_event.dart';
export 'src/reservations/reservation_rules.dart';
export 'src/reservations/reservations_repository.dart';
export 'src/saddles/saddle_list_item.dart';
export 'src/saddles/saddles_repository.dart';
