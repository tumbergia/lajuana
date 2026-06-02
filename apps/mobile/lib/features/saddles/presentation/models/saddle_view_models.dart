import '../../../../app/widgets/app_badge.dart';

class SaddleRecord {
  const SaddleRecord({
    required this.id,
    required this.code,
    required this.name,
    required this.isAvailable,
    this.notes,
    bool isDeleted = false,
  }) : _isDeleted = isDeleted;

  final String id;
  final String code;
  final String name;
  final bool isAvailable;
  final String? notes;
  final bool? _isDeleted;

  /// Null‑safe: defaults to false if hot‑reload left it uninitialized.
  bool get isDeleted => _isDeleted ?? false;

  String get statusLabel {
    if (isDeleted) return 'Eliminada';
    return isAvailable ? 'Disponible' : 'No disponible';
  }

  AppBadgeTone get statusTone {
    if (isDeleted) return AppBadgeTone.danger;
    return isAvailable ? AppBadgeTone.success : AppBadgeTone.neutral;
  }
}

class SaddlePresentationFixtures {
  const SaddlePresentationFixtures._();

  static const List<SaddleRecord> saddles = <SaddleRecord>[];
}
