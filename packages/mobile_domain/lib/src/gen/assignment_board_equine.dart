// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentBoardEquineSchema`.

class AssignmentBoardEquine {
  final String id;
  final String name;
  final String? maxRiderWeightKg;
  final String? imageBase64;
  final String? blockReason;

  const AssignmentBoardEquine({
    required this.id,
    required this.name,
    this.maxRiderWeightKg,
    this.imageBase64,
    this.blockReason,
  });

  factory AssignmentBoardEquine.fromJson(Map<String, dynamic> json) {
    return AssignmentBoardEquine(
      id: json['id'] as String,
      name: json['name'] as String,
      maxRiderWeightKg: json['max_rider_weight_kg'] as String?,
      imageBase64: json['image_base64'] as String?,
      blockReason: json['block_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'max_rider_weight_kg': maxRiderWeightKg,
    'image_base64': imageBase64,
    'block_reason': blockReason,
  };
}
