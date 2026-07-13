// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `InAppUnreadCountSchema`.

class InAppUnreadCount {

  final int unreadCount;

  const InAppUnreadCount(
    {
    required this.unreadCount,
    }
  );

  factory InAppUnreadCount.fromJson(Map<String, dynamic> json) {
    return InAppUnreadCount(
      unreadCount: json['unread_count'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'unread_count': unreadCount,
  };

}
