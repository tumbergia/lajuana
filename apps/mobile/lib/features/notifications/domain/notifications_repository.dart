import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';
import 'package:mobile/features/notifications/infrastructure/notifications_api_client.dart';

abstract class NotificationsRepository {
  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  });

  Future<int> unreadCount();

  Future<InAppNotification> markRead(String notificationId);

  Future<void> markAllRead();

  Future<int> deleteOne(String notificationId);

  Future<int> clearInbox({bool readOnly = false});

  Future<NotificationPreferences> getPreferences();

  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  );
}

class NotificationsRepositoryImpl implements NotificationsRepository {
  NotificationsRepositoryImpl({required NotificationsApiClient apiClient})
    : _api = apiClient;

  final NotificationsApiClient _api;

  @override
  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  }) => _api.listInApp(limit: limit, beforeId: beforeId, unreadOnly: unreadOnly);

  @override
  Future<int> unreadCount() => _api.unreadCount();

  @override
  Future<InAppNotification> markRead(String notificationId) =>
      _api.markRead(notificationId);

  @override
  Future<void> markAllRead() => _api.markAllRead();

  @override
  Future<int> deleteOne(String notificationId) => _api.deleteOne(notificationId);

  @override
  Future<int> clearInbox({bool readOnly = false}) =>
      _api.clearInbox(readOnly: readOnly);

  @override
  Future<NotificationPreferences> getPreferences() => _api.getPreferences();

  @override
  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  ) => _api.updatePreferences(preferences);
}
