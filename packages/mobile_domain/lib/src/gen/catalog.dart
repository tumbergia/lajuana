// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `CatalogResponse`.

import 'catalog_module.dart';

class Catalog {

  final List<CatalogModule> modules;
  final int? schemaVersion;
  final DateTime generatedAt;

  const Catalog(
    {
    required this.modules,
    this.schemaVersion,
    required this.generatedAt,
    }
  );

  factory Catalog.fromJson(Map<String, dynamic> json) {
    return Catalog(
      modules: (json['modules'] as List<dynamic>)
        .map((e) => CatalogModule.fromJson(e as Map<String, dynamic>)).toList(),
      schemaVersion: json['schema_version'] as int?,
      generatedAt: DateTime.parse(json['generated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'modules': modules.map((e) => e.toJson()).toList(),
    'schema_version': schemaVersion,
    'generated_at': generatedAt.toIso8601String(),
  };

}
