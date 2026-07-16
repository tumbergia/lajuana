import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';
import 'package:mobile/features/notifications/domain/notifications_repository.dart';
import 'package:mobile/features/notifications/infrastructure/notification_background_service.dart';
import 'package:mobile/features/notifications/presentation/notification_content.dart';

enum NotificationsLoadState { idle, loading, success, error }

class NotificationsController extends ChangeNotifier {
  NotificationsController({
    required NotificationsRepository repository,
    this.foregroundPollInterval = const Duration(seconds: 20),
  }) : _repository = repository;

  final NotificationsRepository _repository;
  final Duration foregroundPollInterval;

  NotificationsLoadState loadState = NotificationsLoadState.idle;
  List<InAppNotification> items = const [];
  int unreadCount = 0;
  String? errorMessage;
  NotificationPreferences? preferences;
  bool preferencesLoading = false;
  bool backgroundPollingEnabled = true;

  /// Title of the newest notification when unread grew while inbox is hidden.
  String? pendingArrivalTitle;

  /// Body preview for the heads-up toast.
  String? pendingArrivalBody;

  /// Id of the newest notification to open on toast tap.
  String? pendingArrivalId;

  /// Event type of the newest arrival (for icon/color).
  String? pendingArrivalEventType;

  /// How many new unread arrived in the last poll that triggered the banner.
  int pendingArrivalCount = 0;

  bool get hasArrivalBanner =>
      pendingArrivalCount > 0 &&
      pendingArrivalTitle != null &&
      pendingArrivalTitle!.isNotEmpty;

  Timer? _pollTimer;
  bool _listVisible = false;
  bool _loadingList = false;

  /// After the first successful sync we know the current inbox baseline.
  /// Until then, existing unread must not be treated as brand-new arrivals
  /// (that spam local notifications on cold start).
  bool _baselineReady = false;

  Future<void> loadInitial() async {
    if (_loadingList) return;
    _loadingList = true;
    loadState = NotificationsLoadState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      final results = await Future.wait([
        _repository.listInApp(),
        _repository.unreadCount(),
      ]);
      items = results[0] as List<InAppNotification>;
      unreadCount = results[1] as int;
      loadState = NotificationsLoadState.success;
      _seedBaselineFromCurrentInbox();
    } catch (error) {
      errorMessage = error.toString();
      loadState = NotificationsLoadState.error;
    } finally {
      _loadingList = false;
      notifyListeners();
    }
  }

  /// Soft refresh used by polling: updates unread and reloads the list when
  /// needed without forcing a full-screen loader.
  Future<void> refreshQuietly({bool forceList = false}) async {
    try {
      final previousUnread = unreadCount;
      final nextUnread = await _repository.unreadCount();
      final shouldReloadList = forceList ||
          _listVisible ||
          nextUnread != previousUnread ||
          (nextUnread > 0 && items.isEmpty) ||
          !_baselineReady;

      unreadCount = nextUnread;

      if (shouldReloadList) {
        items = await _repository.listInApp();
        if (loadState == NotificationsLoadState.idle ||
            loadState == NotificationsLoadState.error) {
          loadState = NotificationsLoadState.success;
        }
      }

      if (!_baselineReady) {
        _seedBaselineFromCurrentInbox();
        notifyListeners();
        return;
      }

      if (nextUnread > previousUnread && !_listVisible) {
        pendingArrivalCount = nextUnread - previousUnread;
        if (items.isNotEmpty) {
          final newest = items.first;
          final arrival = NotificationArrivalCopy.from(
            eventType: newest.eventType,
            title: newest.title,
            body: newest.body,
            contactPhone: newest.contactPhone,
            count: pendingArrivalCount,
          );
          pendingArrivalTitle = arrival.headline;
          pendingArrivalBody = newest.body;
          pendingArrivalId = newest.id;
          pendingArrivalEventType = newest.eventType;
          unawaited(
            NotificationBackgroundService.showLocal(
              title: arrival.label,
              body: arrival.headline,
              id: pendingArrivalId?.hashCode ??
                  DateTime.now().millisecondsSinceEpoch,
            ),
          );
          unawaited(
            NotificationBackgroundService.markLastSeenId(pendingArrivalId),
          );
        } else {
          pendingArrivalTitle = 'Tienes notificaciones nuevas';
          pendingArrivalBody = null;
          pendingArrivalId = null;
          pendingArrivalEventType = null;
          unawaited(
            NotificationBackgroundService.showLocal(
              title: 'La Juana',
              body: pendingArrivalTitle!,
              id: DateTime.now().millisecondsSinceEpoch,
            ),
          );
        }
      }

      notifyListeners();
    } catch (_) {
      // Best-effort polling; ignore transient errors.
    }
  }

  void _seedBaselineFromCurrentInbox() {
    _baselineReady = true;
    if (items.isNotEmpty) {
      unawaited(NotificationBackgroundService.markLastSeenId(items.first.id));
    }
  }

  Future<void> refreshUnreadCount() => refreshQuietly();

  void dismissArrivalBanner() {
    if (!hasArrivalBanner) return;
    pendingArrivalTitle = null;
    pendingArrivalBody = null;
    pendingArrivalId = null;
    pendingArrivalEventType = null;
    pendingArrivalCount = 0;
    notifyListeners();
  }

  void setListVisible(bool visible) {
    _listVisible = visible;
    if (visible) {
      dismissArrivalBanner();
      unawaited(refreshQuietly(forceList: true));
    }
  }

  void startForegroundPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(foregroundPollInterval, (_) {
      unawaited(refreshQuietly());
    });
    unawaited(refreshQuietly(forceList: true));
  }

  void stopForegroundPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  Future<void> markRead(String notificationId) async {
    try {
      final updated = await _repository.markRead(notificationId);
      items = [
        for (final item in items)
          if (item.id == notificationId) updated else item,
      ];
      unreadCount = items.where((item) => !item.read).length;
      notifyListeners();
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
    }
  }

  Future<void> markAllRead() async {
    try {
      await _repository.markAllRead();
      items = [
        for (final item in items)
          InAppNotification(
            version: item.version,
            createdAt: item.createdAt,
            updatedAt: item.updatedAt,
            deletedAt: item.deletedAt,
            id: item.id,
            userId: item.userId,
            reservationId: item.reservationId,
            title: item.title,
            body: item.body,
            read: true,
            eventType: item.eventType,
            contactPhone: item.contactPhone,
          ),
      ];
      unreadCount = 0;
      notifyListeners();
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
    }
  }

  Future<void> deleteOne(String notificationId) async {
    try {
      await _repository.deleteOne(notificationId);
      final wasUnread = items.any((item) => item.id == notificationId && !item.read);
      items = [for (final item in items) if (item.id != notificationId) item];
      if (wasUnread && unreadCount > 0) {
        unreadCount -= 1;
      }
      notifyListeners();
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> clearInbox({bool readOnly = false}) async {
    try {
      await _repository.clearInbox(readOnly: readOnly);
      if (readOnly) {
        items = [for (final item in items) if (!item.read) item];
      } else {
        items = const [];
        unreadCount = 0;
      }
      notifyListeners();
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> loadPreferences() async {
    preferencesLoading = true;
    notifyListeners();
    try {
      preferences = await _repository.getPreferences();
    } catch (error) {
      errorMessage = error.toString();
    }
    preferencesLoading = false;
    notifyListeners();
  }

  /// Envía un mensaje de WhatsApp directamente a través de la API del backend.
  /// Retorna `true` si se envió correctamente, `false` si falló.
  Future<bool> sendWhatsAppMessage({
    required String phone,
    required String message,
  }) async {
    try {
      await _repository.sendWhatsAppMessage(phone: phone, message: message);
      return true;
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> setPreference(String key, bool enabled) async {
    final current = Map<String, bool>.from(preferences?.preferences ?? {});
    current[key] = enabled;
    try {
      preferences = await _repository.updatePreferences(current);
      notifyListeners();
    } catch (error) {
      errorMessage = error.toString();
      notifyListeners();
    }
  }

  void setBackgroundPollingEnabled(bool enabled) {
    backgroundPollingEnabled = enabled;
    notifyListeners();
  }

  @override
  void dispose() {
    stopForegroundPolling();
    super.dispose();
  }
}
