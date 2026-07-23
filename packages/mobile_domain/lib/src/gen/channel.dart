// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Channel`.

enum Channel {
  FACEBOOK("facebook"),
  INSTAGRAM("instagram"),
  WHATSAPP("whatsapp"),
  EMAIL("email"),
;

  final String value;
  const Channel(this.value);
}

extension ChannelX on Channel {
  String toJson() => value;
}

extension ChannelParse on String {
  Channel toChannel() => Channel.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown Channel: ${this}'),
  );
}

