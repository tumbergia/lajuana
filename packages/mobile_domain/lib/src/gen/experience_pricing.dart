// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperiencePricingSchema`.

import 'experience_pricing_tier.dart';

class ExperiencePricing {
  final String? currency;
  final bool? pricesAreNet;
  final String? pricingNotes;
  final List<ExperiencePricingTier>? tiers;
  final bool? requireContiguousTiers;

  const ExperiencePricing({
    this.currency,
    this.pricesAreNet,
    this.pricingNotes,
    this.tiers,
    this.requireContiguousTiers,
  });

  factory ExperiencePricing.fromJson(Map<String, dynamic> json) {
    return ExperiencePricing(
      currency: json['currency'] as String?,
      pricesAreNet: json['prices_are_net'] as bool?,
      pricingNotes: json['pricing_notes'] as String?,
      tiers: (json['tiers'] as List<dynamic>?)
          ?.map(
            (e) => ExperiencePricingTier.fromJson(e as Map<String, dynamic>),
          )
          .toList(),
      requireContiguousTiers: json['require_contiguous_tiers'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'currency': currency,
    'prices_are_net': pricesAreNet,
    'pricing_notes': pricingNotes,
    'tiers': tiers?.map((e) => e.toJson()).toList(),
    'require_contiguous_tiers': requireContiguousTiers,
  };
}
