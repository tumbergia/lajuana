class UserRecord {
  const UserRecord({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.isActive,
  });

  final String id;
  final String email;
  final String fullName;
  final String role;
  final bool isActive;

  factory UserRecord.fromJson(Map<String, dynamic> json) {
    return UserRecord(
      id: (json['id'] as String?) ?? '',
      email: (json['email'] as String?) ?? '',
      fullName: (json['full_name'] as String?) ?? '',
      role: (json['role'] as String?) ?? 'unassigned',
      isActive: (json['is_active'] as bool?) ?? true,
    );
  }
}

class RoleRequestRecord {
  const RoleRequestRecord({
    required this.id,
    required this.userId,
    required this.userEmail,
    required this.userFullName,
    required this.userRole,
    required this.requestedRole,
    required this.status,
    this.decidedRole,
    this.decidedBy,
    this.decidedAt,
    this.note,
  });

  final String id;
  final String userId;
  final String userEmail;
  final String userFullName;
  final String userRole;
  final String requestedRole;
  final String status;
  final String? decidedRole;
  final String? decidedBy;
  final DateTime? decidedAt;
  final String? note;

  factory RoleRequestRecord.fromJson(Map<String, dynamic> json) {
    final decidedAtRaw = json['decided_at'];
    return RoleRequestRecord(
      id: (json['id'] as String?) ?? '',
      userId: (json['user_id'] as String?) ?? '',
      userEmail: (json['user_email'] as String?) ?? '',
      userFullName: (json['user_full_name'] as String?) ?? '',
      userRole: (json['user_role'] as String?) ?? 'unassigned',
      requestedRole: (json['requested_role'] as String?) ?? 'guide',
      status: (json['status'] as String?) ?? 'pending',
      decidedRole: json['decided_role'] as String?,
      decidedBy: json['decided_by'] as String?,
      decidedAt: decidedAtRaw is String ? DateTime.tryParse(decidedAtRaw) : null,
      note: json['note'] as String?,
    );
  }
}
