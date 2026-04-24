class CatalogEmergencyContact {
  const CatalogEmergencyContact({
    required this.code,
    required this.name,
    required this.description,
    required this.phoneNumber,
    required this.category,
    required this.isPrimary,
    required this.isNational,
  });

  final String code;
  final String name;
  final String description;
  final String phoneNumber;
  final String category;
  final bool isPrimary;
  final bool isNational;
}
