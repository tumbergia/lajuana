// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperiencePricingTierSchema`.

class ExperiencePricingTier {

  final int minParticipants;
  final int maxParticipants;
  final int pricePerPerson;

  const ExperiencePricingTier(
    {
    required this.minParticipants,
    required this.maxParticipants,
    required this.pricePerPerson,
    }
  );

  factory ExperiencePricingTier.fromJson(Map<String, dynamic> json) {
    return ExperiencePricingTier(
      minParticipants: json['min_participants'] as int,
      maxParticipants: json['max_participants'] as int,
      pricePerPerson: json['price_per_person'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'min_participants': minParticipants,
    'max_participants': maxParticipants,
    'price_per_person': pricePerPerson,
  };

}
