// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `LeadsPreferencesSchema`.

class LeadsPreferences {

  final List<String>? pinnedLeadIds;
  final List<String>? excludedLeadIds;

  const LeadsPreferences(
    {
    this.pinnedLeadIds,
    this.excludedLeadIds,
    }
  );

  factory LeadsPreferences.fromJson(Map<String, dynamic> json) {
    return LeadsPreferences(
      pinnedLeadIds: (json['pinned_lead_ids'] as List<dynamic>?)
        ?.cast<String>(),
      excludedLeadIds: (json['excluded_lead_ids'] as List<dynamic>?)
        ?.cast<String>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'pinned_lead_ids': pinnedLeadIds,
    'excluded_lead_ids': excludedLeadIds,
  };

}
