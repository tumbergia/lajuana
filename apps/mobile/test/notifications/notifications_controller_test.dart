import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';
import 'package:mobile/features/notifications/domain/notifications_repository.dart';
import 'package:mobile/features/notifications/presentation/controllers/notifications_controller.dart';

class _FakeNotificationsRepository implements NotificationsRepository {
  List<InAppNotification> items = [];
  int unread = 0;
  NotificationPreferences prefs = const NotificationPreferences(
    preferences: {'reservation_created': true},
  );
  bool shouldThrow = false;
  int deleteOneCalls = 0;
  int clearInboxCalls = 0;
  bool? lastClearReadOnly;

  @override
  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  }) async {
    if (shouldThrow) throw Exception('network');
    if (unreadOnly) return items.where((item) => !item.read).toList();
    return items;
  }

  @override
  Future<int> unreadCount() async {
    if (shouldThrow) throw Exception('network');
    return unread;
  }

  @override
  Future<InAppNotification> markRead(String notificationId) async {
    items = [
      for (final item in items)
        if (item.id == notificationId)
          InAppNotification(
            version: item.version,
            createdAt: item.createdAt,
            updatedAt: item.updatedAt,
            id: item.id,
            userId: item.userId,
            reservationId: item.reservationId,
            title: item.title,
            body: item.body,
            read: true,
            eventType: item.eventType,
            contactPhone: item.contactPhone,
          )
        else
          item,
    ];
    unread = items.where((item) => !item.read).length;
    return items.firstWhere((item) => item.id == notificationId);
  }

  @override
  Future<void> markAllRead() async {
    items = [
      for (final item in items)
        InAppNotification(
          version: item.version,
          createdAt: item.createdAt,
          updatedAt: item.updatedAt,
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
    unread = 0;
  }

  @override
  Future<int> deleteOne(String notificationId) async {
    deleteOneCalls += 1;
    final before = items.length;
    items = [for (final item in items) if (item.id != notificationId) item];
    unread = items.where((item) => !item.read).length;
    return before - items.length;
  }

  @override
  Future<int> clearInbox({bool readOnly = false}) async {
    clearInboxCalls += 1;
    lastClearReadOnly = readOnly;
    final before = items.length;
    if (readOnly) {
      items = [for (final item in items) if (!item.read) item];
    } else {
      items = [];
      unread = 0;
    }
    return before - items.length;
  }

  @override
  Future<NotificationPreferences> getPreferences() async => prefs;

  @override
  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  ) async {
    prefs = NotificationPreferences(preferences: preferences);
    return prefs;
  }

  @override
  Future<void> sendWhatsAppMessage({
    required String phone,
    required String message,
  }) async {
    // No-op in tests.
  }
}

InAppNotification _item({
  required String id,
  bool read = false,
  String title = 'Título',
  String? contactPhone,
}) {
  final now = DateTime.utc(2026, 7, 13, 12);
  return InAppNotification(
    version: 1,
    createdAt: now,
    updatedAt: now,
    id: id,
    userId: 'user-1',
    reservationId: 'res-1',
    title: title,
    body: 'Cuerpo',
    read: read,
    eventType: 'reservation_created',
    contactPhone: contactPhone,
  );
}

void main() {
  late _FakeNotificationsRepository repository;
  late NotificationsController controller;

  setUp(() {
    repository = _FakeNotificationsRepository();
    controller = NotificationsController(repository: repository);
  });

  tearDown(() => controller.dispose());

  test('loadInitial transitions to success and sets unread', () async {
    repository.items = [_item(id: '1'), _item(id: '2', read: true)];
    repository.unread = 1;

    await controller.loadInitial();

    expect(controller.loadState, NotificationsLoadState.success);
    expect(controller.items, hasLength(2));
    expect(controller.unreadCount, 1);
  });

  test('refreshQuietly reloads list when unread grows', () async {
    repository.items = [];
    repository.unread = 0;
    await controller.loadInitial();
    expect(controller.items, isEmpty);

    repository.items = [_item(id: '1')];
    repository.unread = 1;
    await controller.refreshQuietly();

    expect(controller.unreadCount, 1);
    expect(controller.items, hasLength(1));
  });

  test('setListVisible forces list refresh', () async {
    repository.items = [_item(id: '1')];
    repository.unread = 1;
    controller.setListVisible(true);
    await Future<void>.delayed(Duration.zero);
    // Allow the unawaited refresh to complete.
    await controller.refreshQuietly(forceList: true);
    expect(controller.items, hasLength(1));
  });

  test('loadInitial transitions to error', () async {
    repository.shouldThrow = true;
    await controller.loadInitial();
    expect(controller.loadState, NotificationsLoadState.error);
    expect(controller.errorMessage, isNotNull);
    expect(controller.errorMessage, isNot(contains('Exception')));
    expect(
      controller.errorMessage,
      'No se pudieron cargar las notificaciones.',
    );
  });

  test('markRead updates item and unread count', () async {
    repository.items = [_item(id: '1'), _item(id: '2')];
    repository.unread = 2;
    await controller.loadInitial();

    await controller.markRead('1');

    expect(controller.items.firstWhere((item) => item.id == '1').read, isTrue);
    expect(controller.unreadCount, 1);
  });

  test('markAllRead clears unread', () async {
    repository.items = [_item(id: '1'), _item(id: '2')];
    repository.unread = 2;
    await controller.loadInitial();

    await controller.markAllRead();

    expect(controller.unreadCount, 0);
    expect(controller.items.every((item) => item.read), isTrue);
  });

  test('deleteOne removes item and decrements unread', () async {
    repository.items = [_item(id: '1'), _item(id: '2', read: true)];
    repository.unread = 1;
    await controller.loadInitial();

    await controller.deleteOne('1');

    expect(repository.deleteOneCalls, 1);
    expect(controller.items.map((item) => item.id), ['2']);
    expect(controller.unreadCount, 0);
  });

  test('clearInbox readOnly keeps unread items', () async {
    repository.items = [_item(id: '1'), _item(id: '2', read: true)];
    repository.unread = 1;
    await controller.loadInitial();

    await controller.clearInbox(readOnly: true);

    expect(repository.clearInboxCalls, 1);
    expect(repository.lastClearReadOnly, isTrue);
    expect(controller.items.map((item) => item.id), ['1']);
    expect(controller.unreadCount, 1);
  });

  test('clearInbox all empties list and unread', () async {
    repository.items = [_item(id: '1'), _item(id: '2', read: true)];
    repository.unread = 1;
    await controller.loadInitial();

    await controller.clearInbox();

    expect(repository.lastClearReadOnly, isFalse);
    expect(controller.items, isEmpty);
    expect(controller.unreadCount, 0);
  });

  test('setPreference updates preferences map', () async {
    await controller.loadPreferences();
    await controller.setPreference('reservation_created', false);
    expect(controller.preferences?.preferences?['reservation_created'], isFalse);
  });

  test('refreshQuietly sets arrival banner when unread grows while hidden', () async {
    repository.items = [];
    repository.unread = 0;
    await controller.loadInitial();
    expect(controller.hasArrivalBanner, isFalse);

    repository.items = [
      _item(id: '1', title: 'Nueva reserva'),
      _item(id: '2', title: 'Otro'),
    ];
    repository.unread = 2;
    await controller.refreshQuietly();

    expect(controller.hasArrivalBanner, isTrue);
    expect(controller.pendingArrivalCount, 2);
    // Parsed headline (same as inbox / push), not the raw API title.
    expect(controller.pendingArrivalTitle, 'Cuerpo');
    expect(controller.pendingArrivalId, '1');
  });

  test('first quiet refresh seeds baseline without arrival spam', () async {
    repository.items = [
      _item(id: '1', title: 'Ya estaba'),
      _item(id: '2', title: 'También'),
    ];
    repository.unread = 2;

    await controller.refreshQuietly(forceList: true);

    expect(controller.unreadCount, 2);
    expect(controller.items, hasLength(2));
    expect(controller.hasArrivalBanner, isFalse);
    expect(controller.pendingArrivalCount, 0);

    repository.items = [
      _item(id: '3', title: 'Nueva'),
      ...repository.items,
    ];
    repository.unread = 3;
    await controller.refreshQuietly();

    expect(controller.hasArrivalBanner, isTrue);
    expect(controller.pendingArrivalCount, 1);
    expect(controller.pendingArrivalId, '3');
  });

  test('refreshQuietly formats status tokens for arrival banner', () async {
    repository.items = [];
    repository.unread = 0;
    await controller.loadInitial();

    repository.items = [
      InAppNotification(
        version: 1,
        createdAt: DateTime.utc(2026, 7, 13, 12),
        updatedAt: DateTime.utc(2026, 7, 13, 12),
        id: 'status-1',
        userId: 'user-1',
        reservationId: 'res-1',
        title: 'Estado de reserva actualizado',
        body: 'Ana Pérez — RES-TEST: quoted → confirmed',
        read: false,
        eventType: 'reservation_status_changed',
      ),
    ];
    repository.unread = 1;
    await controller.refreshQuietly();

    expect(controller.pendingArrivalTitle, 'Cotizado → Confirmada');
  });

  test('refreshQuietly does not set arrival banner when list is visible', () async {
    repository.items = [];
    repository.unread = 0;
    await controller.loadInitial();
    controller.setListVisible(true);
    await Future<void>.delayed(Duration.zero);
    await controller.refreshQuietly(forceList: true);

    repository.items = [_item(id: '1', title: 'Nueva')];
    repository.unread = 1;
    await controller.refreshQuietly();

    expect(controller.hasArrivalBanner, isFalse);
  });

  test('dismissArrivalBanner and setListVisible clear arrival signal', () async {
    repository.items = [];
    repository.unread = 0;
    await controller.loadInitial();
    repository.items = [_item(id: '1', title: 'Hola')];
    repository.unread = 1;
    await controller.refreshQuietly();
    expect(controller.hasArrivalBanner, isTrue);

    controller.dismissArrivalBanner();
    expect(controller.hasArrivalBanner, isFalse);
    expect(controller.pendingArrivalCount, 0);
    expect(controller.pendingArrivalTitle, isNull);
    expect(controller.pendingArrivalId, isNull);

    repository.items = [_item(id: '2', title: 'Otra')];
    repository.unread = 2;
    await controller.refreshQuietly();
    expect(controller.hasArrivalBanner, isTrue);

    controller.setListVisible(true);
    expect(controller.hasArrivalBanner, isFalse);
  });
}
