class SaddleListItem {
  const SaddleListItem({
    required this.id,
    required this.code,
    this.name,
    required this.isAvailable,
    this.notes,
    this.deletedAt,
  });

  final String id;
  final String code;
  final String? name;
  final bool isAvailable;
  final String? notes;
  final DateTime? deletedAt;

  bool get isDeleted => deletedAt != null;

  factory SaddleListItem.fromJson(Map<String, dynamic> json) {
    return SaddleListItem(
      id: json['id'] as String? ?? '',
      code: json['code'] as String? ?? '',
      name: json['name'] as String?,
      isAvailable: json['is_available'] as bool? ?? true,
      notes: json['notes'] as String?,
      deletedAt: json['deleted_at'] != null
          ? DateTime.parse(json['deleted_at'] as String).toUtc()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'code': code,
      if (name != null) 'name': name,
      'is_available': isAvailable,
      if (notes != null) 'notes': notes,
    };
  }
}
