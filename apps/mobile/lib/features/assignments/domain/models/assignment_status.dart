/// Mirror of backend AssignmentStatus and AssignmentSource enums.
enum AssignmentStatus {
  draft,
  confirmed,
  final_,
  replaced,
  cancelled;

  String get apiValue {
    if (this == AssignmentStatus.final_) return 'final';
    return name;
  }

  static AssignmentStatus fromApi(String value) {
    if (value == 'final') return AssignmentStatus.final_;
    return AssignmentStatus.values.firstWhere(
      (e) => e.name == value,
      orElse: () => AssignmentStatus.draft,
    );
  }
}

enum AssignmentSource {
  manualAdmin,
  manualGuide,
  systemSuggested;

  String get apiValue {
    switch (this) {
      case AssignmentSource.manualAdmin:
        return 'manual_admin';
      case AssignmentSource.manualGuide:
        return 'manual_guide';
      case AssignmentSource.systemSuggested:
        return 'system_suggested';
    }
  }

  static AssignmentSource fromApi(String value) {
    switch (value) {
      case 'manual_admin':
        return AssignmentSource.manualAdmin;
      case 'manual_guide':
        return AssignmentSource.manualGuide;
      case 'system_suggested':
        return AssignmentSource.systemSuggested;
      default:
        return AssignmentSource.manualAdmin;
    }
  }
}
