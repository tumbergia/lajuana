class SaddleListItem {
  const SaddleListItem({
    required this.id,
    required this.code,
    this.name,
    required this.isAvailable,
    this.notes,
    this.isDeleted = false,
  });

  final String id;
  final String code;
  final String? name;
  final bool isAvailable;
  final String? notes;
  final bool isDeleted;
}
