// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ProviderType`.

enum ProviderType {
  LODGING("lodging"),
  FOOD("food"),
  TRANSPORT_PEOPLE("transport_people"),
  EQUINE_TRANSPORT("equine_transport"),
  EXPERIENCE_ALLY("experience_ally"),
  GUIDE_ALLY("guide_ally"),
  PARK_OR_ACCESS("park_or_access"),
  INSURANCE("insurance"),
  OTHER("other");

  final String value;
  const ProviderType(this.value);
}

extension ProviderTypeX on ProviderType {
  String toJson() => value;
}

extension ProviderTypeParse on String {
  ProviderType toProviderType() => ProviderType.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ProviderType: ${this}'),
  );
}
