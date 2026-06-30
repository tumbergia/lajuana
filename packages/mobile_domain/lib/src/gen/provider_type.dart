// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ProviderType`.

enum ProviderType {
  @JsonValue('lodging')
  LODGING("lodging"),
  @JsonValue('food')
  FOOD("food"),
  @JsonValue('transport_people')
  TRANSPORT_PEOPLE("transport_people"),
  @JsonValue('equine_transport')
  EQUINE_TRANSPORT("equine_transport"),
  @JsonValue('experience_ally')
  EXPERIENCE_ALLY("experience_ally"),
  @JsonValue('guide_ally')
  GUIDE_ALLY("guide_ally"),
  @JsonValue('park_or_access')
  PARK_OR_ACCESS("park_or_access"),
  @JsonValue('insurance')
  INSURANCE("insurance"),
  @JsonValue('other')
  OTHER("other"),
;

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

