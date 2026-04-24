import '../../../../app/widgets/app_badge.dart';

class EquineDemoRecord {
  const EquineDemoRecord({
    required this.name,
    required this.summary,
    required this.statusLabel,
    required this.statusTone,
  });

  final String name;
  final String summary;
  final String statusLabel;
  final AppBadgeTone statusTone;
}
