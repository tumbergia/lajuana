// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `CatalogModuleSize`.

enum CatalogModuleSize {
  COMPACT("compact"),
  STANDARD("standard"),
  WIDE("wide"),
;

  final String value;
  const CatalogModuleSize(this.value);
}

extension CatalogModuleSizeX on CatalogModuleSize {
  String toJson() => value;
}

extension CatalogModuleSizeParse on String {
  CatalogModuleSize toCatalogModuleSize() => CatalogModuleSize.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown CatalogModuleSize: ${this}'),
  );
}

