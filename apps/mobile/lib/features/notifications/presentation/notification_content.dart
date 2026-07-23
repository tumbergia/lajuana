import 'package:mobile/features/notifications/presentation/notification_visuals.dart';
import 'package:mobile_domain/mobile_domain.dart';

class NotificationFact {
  const NotificationFact({required this.label, required this.value});

  final String label;
  final String value;
}

/// Parsed, user-friendly presentation of an in-app notification.
class NotificationContent {
  const NotificationContent({
    required this.headline,
    this.keyFacts = const [],
    this.detailLines = const [],
    this.isQuotedMessage = false,
    this.paymentProofId,
  });

  /// Large primary text (what happened / message preview).
  final String headline;

  /// Structured bits for list compact line and detail rows.
  final List<NotificationFact> keyFacts;

  /// Extra lines for detail (e.g. tomorrow bullet list). Empty = use keyFacts only.
  final List<String> detailLines;

  /// When true, detail should render [headline] as a quoted message block.
  final bool isQuotedMessage;

  /// Payment proof id embedded in body when available.
  final String? paymentProofId;

  String get previewLine {
    final line = headline.trim();
    if (line.isEmpty) return '';
    final first = line.split('\n').first.trim();
    return first;
  }

  /// Compact key facts for the list subtitle (max 3).
  String get compactFacts {
    final parts = <String>[];
    for (final fact in keyFacts) {
      if (parts.length >= 3) break;
      final value = fact.value.trim();
      if (value.isEmpty) continue;
      // Skip facts that already appear in the headline.
      if (headline.contains(value)) continue;
      parts.add(value);
    }
    return parts.join(' · ');
  }

  factory NotificationContent.from({
    required String eventType,
    required String title,
    required String body,
    String? contactPhone,
  }) {
    final trimmedBody = body.trim();
    final trimmedTitle = title.trim();
    final phone = resolveNotificationPhone(
      contactPhone: contactPhone,
      body: trimmedBody,
    );
    final looksCancelled =
        trimmedBody.toLowerCase().contains('cancel') ||
        trimmedTitle.toLowerCase().contains('cancel');

    return switch (eventType) {
      'reservation_created' => _reservationCreated(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'reservation_confirmed' => _reservationConfirmed(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'reservation_cancelled' => _reservationCancelled(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'reservation_status_changed' when looksCancelled => _reservationCancelled(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'reservation_status_changed' => _reservationStatusChanged(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'reservation_updated' => _reservationUpdated(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'payment_proof_registered' => _paymentProof(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'participant_form_completed' => _participantForm(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'human_review_requested' || 'whatsapp_message_unattended' =>
        _whatsAppMessage(trimmedBody, trimmedTitle, phone),
      'whatsapp_delivery_failed' => _whatsAppDeliveryFailed(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'configuration_changed' => _configurationChanged(
        trimmedBody,
        trimmedTitle,
      ),
      'assignment_changed' => _assignmentChanged(
        trimmedBody,
        trimmedTitle,
        phone,
      ),
      'tomorrow_services_summary' => _tomorrowSummary(
        trimmedBody,
        trimmedTitle,
      ),
      'role_request_created' ||
      'role_request_decided' => _roleRequest(trimmedBody, trimmedTitle),
      _ => _fallback(trimmedBody, trimmedTitle),
    };
  }
}

/// Copy shared by in-app heads-up toast and local/system push notifications.
class NotificationArrivalCopy {
  const NotificationArrivalCopy({required this.label, required this.headline});

  /// Top line ("La Juana" or "N notificaciones"), same as heads-up.
  final String label;

  /// Main line with Spanish/humanized content (no raw status tokens).
  final String headline;

  factory NotificationArrivalCopy.from({
    required String eventType,
    required String title,
    required String body,
    String? contactPhone,
    int count = 1,
  }) {
    final content = NotificationContent.from(
      eventType: eventType,
      title: title,
      body: body,
      contactPhone: contactPhone,
    );
    final headline = content.previewLine.isNotEmpty
        ? content.previewLine
        : (title.trim().isNotEmpty ? title.trim() : 'Nueva notificación');
    final label = count > 1 ? '$count notificaciones' : 'La Juana';
    return NotificationArrivalCopy(label: label, headline: headline);
  }
}

String notificationStatusLabel(String raw) {
  final token = raw.trim();
  if (token.isEmpty) return token;
  final lower = token.toLowerCase();
  switch (lower) {
    case 'pending':
      return 'Pendiente';
    case 'approved':
      return 'Aprobada';
    case 'rejected':
      return 'Rechazada';
    case 'cancelled':
    case 'canceled':
      return 'Cancelada';
  }
  final parsed = parseReservationStatus(token);
  if (parsed != ReservationStatus.unknown) {
    return reservationStatusLabel(parsed);
  }
  return _humanizeSnake(token);
}

class TomorrowReservationLine {
  const TomorrowReservationLine({
    required this.code,
    required this.subtitle,
    this.reservationId,
  });

  final String code;
  final String subtitle;
  final String? reservationId;
}

/// Parses "RES-TEST: Ana Pérez (4)" or "RES-TEST|{id}: Ana Pérez (4)".
TomorrowReservationLine? parseTomorrowReservationLine(String line) {
  final trimmed = line.replaceFirst(RegExp(r'^[•\*]\s*'), '').trim();
  if (trimmed.isEmpty) return null;
  if (trimmed.startsWith('…') || trimmed.startsWith('...')) {
    return TomorrowReservationLine(code: 'Más', subtitle: trimmed);
  }
  final match = RegExp(
    r'^(\S+?)(?:\|([a-fA-F0-9]{24}))?:\s*(.+?)(?:\s*\((\d+)\))?\s*$',
  ).firstMatch(trimmed);
  if (match == null) return null;
  final code = match.group(1)!.trim();
  final reservationId = match.group(2)?.trim();
  final holder = match.group(3)!.trim();
  final count = match.group(4)?.trim();
  final subtitle = count == null ? holder : '$holder · $count participantes';
  return TomorrowReservationLine(
    code: code,
    subtitle: subtitle,
    reservationId: reservationId,
  );
}

List<NotificationFact> _withPhone(List<NotificationFact> facts, String? phone) {
  if (phone == null || phone.trim().isEmpty) return facts;
  return [...facts, NotificationFact(label: 'Teléfono', value: phone.trim())];
}

String _humanizeSnake(String raw) {
  const fieldLabels = {
    'holder_name': 'Titular',
    'holder_phone': 'Teléfono',
    'participant_count': 'Participantes',
    'requested_date': 'Fecha',
    'requested_time': 'Hora',
    'experience_id': 'Experiencia',
    'notes': 'Notas',
    'internal_notes': 'Notas internas',
  };
  final key = raw.trim().toLowerCase();
  final mapped = fieldLabels[key];
  if (mapped != null) return mapped;
  if (!key.contains('_')) return raw.trim();
  return key
      .split('_')
      .where((part) => part.isNotEmpty)
      .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
      .join(' ');
}

String _humanizeFieldList(String raw) {
  return raw
      .split(',')
      .map((part) => _humanizeSnake(part.trim()))
      .where((part) => part.isNotEmpty)
      .join(', ');
}

NotificationContent _reservationCreated(
  String body,
  String title,
  String? phone,
) {
  // "{holder} — {code} ({n} participantes)"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*([^\s(]+)\s*\((\d+)\s*participantes?\)\s*$',
  ).firstMatch(body);
  if (match != null) {
    final holder = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    final count = match.group(3)!.trim();
    return NotificationContent(
      headline: '$holder · $count participantes',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
        NotificationFact(label: 'Participantes', value: '$count participantes'),
      ], phone),
    );
  }
  return _holderCodeFallback(body, title, defaultHeadline: title, phone: phone);
}

NotificationContent _reservationConfirmed(
  String body,
  String title,
  String? phone,
) {
  // Template: "Reserva {code} confirmada - {count} participantes."
  final template = RegExp(
    r'^Reserva\s+(\S+)\s+confirmada\s*[-–—]\s*(\d+)\s*participantes\.?$',
    caseSensitive: false,
  ).firstMatch(body);
  if (template != null) {
    final code = template.group(1)!.trim();
    final count = template.group(2)!.trim();
    return NotificationContent(
      headline: 'Confirmada · $count participantes',
      keyFacts: _withPhone([
        NotificationFact(label: 'Código', value: code),
        NotificationFact(label: 'Participantes', value: '$count participantes'),
      ], phone),
    );
  }
  // Sample-style: "{holder} — {code} confirmada…"
  final holderCode = _splitHolderCode(body);
  if (holderCode != null) {
    return NotificationContent(
      headline: '${holderCode.holder} · confirmada',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holderCode.holder),
        NotificationFact(label: 'Código', value: holderCode.code),
      ], phone),
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: _withPhone(const [], phone),
  );
}

NotificationContent _reservationCancelled(
  String body,
  String title,
  String? phone,
) {
  // "{holder} — {code} (antes: {status})"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*([^\s(]+)\s*\(antes:\s*(.+?)\)\s*$',
    caseSensitive: false,
  ).firstMatch(body);
  if (match != null) {
    final holder = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    final previous = notificationStatusLabel(match.group(3)!.trim());
    return NotificationContent(
      headline: '$holder · cancelada',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
        NotificationFact(label: 'Estado anterior', value: previous),
      ], phone),
    );
  }
  final holderCode = _splitHolderCode(body);
  if (holderCode != null) {
    return NotificationContent(
      headline: '${holderCode.holder} · cancelada',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holderCode.holder),
        NotificationFact(label: 'Código', value: holderCode.code),
      ], phone),
    );
  }
  return NotificationContent(
    headline: 'Reserva cancelada',
    keyFacts: _withPhone(const [], phone),
  );
}

NotificationContent _reservationStatusChanged(
  String body,
  String title,
  String? phone,
) {
  // "{holder} — {code}: {prev} → {new}"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*([^:]+):\s*(.+?)\s*→\s*(.+)\s*$',
  ).firstMatch(body);
  if (match != null) {
    final holder = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    final prev = notificationStatusLabel(match.group(3)!.trim());
    final next = notificationStatusLabel(match.group(4)!.trim());
    return NotificationContent(
      headline: '$prev → $next',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
        NotificationFact(label: 'Cambio', value: '$prev → $next'),
      ], phone),
    );
  }
  return _holderCodeFallback(body, title, defaultHeadline: title, phone: phone);
}

NotificationContent _reservationUpdated(
  String body,
  String title,
  String? phone,
) {
  // "{holder} — {code}: {fields}"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*([^:]+):\s*(.+)\s*$',
  ).firstMatch(body);
  if (match != null) {
    final holder = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    final fields = _humanizeFieldList(match.group(3)!.trim());
    return NotificationContent(
      headline: fields.isNotEmpty
          ? 'Se actualizó: $fields'
          : 'Reserva actualizada',
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
        if (fields.isNotEmpty) NotificationFact(label: 'Campos', value: fields),
      ], phone),
    );
  }
  return _holderCodeFallback(body, title, defaultHeadline: title, phone: phone);
}

NotificationContent _paymentProof(String body, String title, String? phone) {
  // "{holder} — {code}: {filename}" or "{holder} — {code}: {filename}|{proofId}"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*([^:]+):\s*(.+)\s*$',
  ).firstMatch(body);
  if (match != null) {
    final holder = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    final rest = match.group(3)!.trim();
    String filename = rest;
    String? proofId;
    final pipe = rest.lastIndexOf('|');
    if (pipe > 0 && pipe < rest.length - 1) {
      final maybeId = rest.substring(pipe + 1).trim();
      if (RegExp(r'^[a-fA-F0-9]{24}$').hasMatch(maybeId)) {
        filename = rest.substring(0, pipe).trim();
        proofId = maybeId;
      }
    }
    return NotificationContent(
      headline: 'Comprobante de $holder',
      paymentProofId: proofId,
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
      ], phone),
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: _withPhone(const [], phone),
  );
}

NotificationContent _participantForm(String body, String title, String? phone) {
  // "{name} — reserva {code}"
  final match = RegExp(
    r'^(.+?)\s*[—–-]\s*reserva\s+(\S+)\s*$',
    caseSensitive: false,
  ).firstMatch(body);
  if (match != null) {
    final name = match.group(1)!.trim();
    return NotificationContent(
      headline: '$name completó el formulario',
      keyFacts: [
        NotificationFact(label: 'Participante', value: name),
        NotificationFact(label: 'Código', value: match.group(2)!.trim()),
        if (phone != null && phone.trim().isNotEmpty)
          NotificationFact(label: 'Teléfono', value: phone.trim()),
      ],
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: [
      if (phone != null && phone.trim().isNotEmpty)
        NotificationFact(label: 'Teléfono', value: phone.trim()),
    ],
  );
}

NotificationContent _whatsAppMessage(String body, String title, String? phone) {
  String message = body;
  final colon = RegExp(
    r'^(\+?\d[\d\s\-]{6,})\s*:\s*(.*)$',
    dotAll: true,
  ).firstMatch(body);
  if (colon != null) {
    message = (colon.group(2) ?? '').trim();
  }
  if (message.isEmpty) message = title;
  return NotificationContent(
    headline: message,
    keyFacts: [
      if (phone != null && phone.trim().isNotEmpty)
        NotificationFact(label: 'Teléfono', value: phone.trim()),
    ],
    isQuotedMessage: true,
  );
}

NotificationContent _whatsAppDeliveryFailed(
  String body,
  String title,
  String? phone,
) {
  // "No se pudo enviar a {phone}: {preview}. {error}"
  final match = RegExp(
    r'^No se pudo enviar a\s+(.+?):\s*(.+)$',
    caseSensitive: false,
  ).firstMatch(body);
  if (match != null) {
    final rest = match.group(2)!.trim();
    String preview = rest;
    String? error;
    final dot = rest.lastIndexOf('. ');
    if (dot > 0 && dot < rest.length - 2) {
      preview = rest.substring(0, dot).trim();
      error = rest.substring(dot + 2).trim();
      if (error.isEmpty) error = null;
    }
    return NotificationContent(
      headline: preview.isNotEmpty ? preview : 'No se pudo enviar el mensaje',
      keyFacts: [
        NotificationFact(
          label: 'Teléfono',
          value: (phone ?? match.group(1)!).trim(),
        ),
        if (error != null) NotificationFact(label: 'Error', value: error),
      ],
      isQuotedMessage: true,
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: [
      if (phone != null && phone.trim().isNotEmpty)
        NotificationFact(label: 'Teléfono', value: phone.trim()),
    ],
  );
}

NotificationContent _configurationChanged(String body, String title) {
  // "{actor} actualizó: {section}"
  final match = RegExp(
    r'^(.+?)\s+actualizó:\s*(.+)\s*$',
    caseSensitive: false,
  ).firstMatch(body);
  if (match != null) {
    final actor = match.group(1)!.trim();
    final section = match.group(2)!.trim();
    return NotificationContent(
      headline: '$actor actualizó $section',
      keyFacts: [
        NotificationFact(label: 'Quién', value: actor),
        NotificationFact(label: 'Sección', value: section),
      ],
    );
  }
  return NotificationContent(headline: body.isNotEmpty ? body : title);
}

NotificationContent _roleRequest(String body, String title) {
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: const [
      NotificationFact(label: 'Tipo', value: 'Solicitud de rol'),
    ],
  );
}

NotificationContent _assignmentChanged(
  String body,
  String title,
  String? phone,
) {
  // New: "Asignación {action} — {holder} · reserva {code}"
  final withHolder = RegExp(
    r'^Asignación\s+(\S+)\s*[—–-]\s*(.+?)\s*·\s*reserva\s+(\S+)\s*$',
    caseSensitive: false,
  ).firstMatch(body);
  if (withHolder != null) {
    final action = withHolder.group(1)!.trim();
    final holder = withHolder.group(2)!.trim();
    final code = withHolder.group(3)!.trim();
    return NotificationContent(
      headline: 'Asignación $action · $holder',
      keyFacts: _withPhone([
        NotificationFact(label: 'Acción', value: action),
        NotificationFact(label: 'Titular', value: holder),
        NotificationFact(label: 'Código', value: code),
      ], phone),
    );
  }
  // Legacy: "Asignación {action} — reserva {code}"
  final match = RegExp(
    r'^Asignación\s+(\S+)\s*[—–-]\s*reserva\s+(\S+)\s*$',
    caseSensitive: false,
  ).firstMatch(body);
  if (match != null) {
    final action = match.group(1)!.trim();
    final code = match.group(2)!.trim();
    return NotificationContent(
      headline: 'Asignación $action · $code',
      keyFacts: _withPhone([
        NotificationFact(label: 'Acción', value: action),
        NotificationFact(label: 'Código', value: code),
      ], phone),
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : title,
    keyFacts: _withPhone(const [], phone),
  );
}

NotificationContent _tomorrowSummary(String body, String title) {
  final lines = body
      .split('\n')
      .map((line) => line.trim())
      .where((line) => line.isNotEmpty)
      .toList(growable: false);
  final countMatch = RegExp(r'\((\d+)\)').firstMatch(title);
  final count = countMatch?.group(1);
  final detailLines = [
    for (final line in lines) line.replaceFirst(RegExp(r'^[•\*]\s*'), ''),
  ];
  return NotificationContent(
    headline: count != null
        ? '$count reservas mañana'
        : (title.isNotEmpty ? title : 'Reservas de mañana'),
    keyFacts: [
      for (final line in detailLines.take(3))
        NotificationFact(
          label: 'Reserva',
          value: parseTomorrowReservationLine(line)?.subtitle ?? line,
        ),
    ],
    detailLines: detailLines,
  );
}

NotificationContent _fallback(String body, String title) {
  return NotificationContent(headline: body.isNotEmpty ? body : title);
}

NotificationContent _holderCodeFallback(
  String body,
  String title, {
  required String defaultHeadline,
  String? phone,
}) {
  final holderCode = _splitHolderCode(body);
  if (holderCode != null) {
    final rest = holderCode.rest;
    final labeledRest = rest == null || rest.isEmpty
        ? null
        : (rest.contains('→')
              ? rest
                    .split('→')
                    .map((part) => notificationStatusLabel(part.trim()))
                    .join(' → ')
              : _humanizeFieldList(rest));
    return NotificationContent(
      headline: labeledRest != null && labeledRest.isNotEmpty
          ? '${holderCode.holder} · $labeledRest'
          : holderCode.holder,
      keyFacts: _withPhone([
        NotificationFact(label: 'Titular', value: holderCode.holder),
        NotificationFact(label: 'Código', value: holderCode.code),
        if (labeledRest != null && labeledRest.isNotEmpty)
          NotificationFact(label: 'Detalle', value: labeledRest),
      ], phone),
    );
  }
  return NotificationContent(
    headline: body.isNotEmpty ? body : defaultHeadline,
    keyFacts: _withPhone(const [], phone),
  );
}

class _HolderCodeParts {
  const _HolderCodeParts({required this.holder, required this.code, this.rest});

  final String holder;
  final String code;
  final String? rest;
}

/// Splits "{holder} — {code}" or "{holder} — {code}: {rest}" / "{holder} — {code} rest".
_HolderCodeParts? _splitHolderCode(String body) {
  final withColon = RegExp(
    r'^(.+?)\s*[—–-]\s*([^:]+):\s*(.+)\s*$',
  ).firstMatch(body);
  if (withColon != null) {
    return _HolderCodeParts(
      holder: withColon.group(1)!.trim(),
      code: withColon.group(2)!.trim(),
      rest: withColon.group(3)!.trim(),
    );
  }
  final plain = RegExp(r'^(.+?)\s*[—–-]\s*(\S+)(?:\s+(.*))?$').firstMatch(body);
  if (plain != null) {
    final rest = plain.group(3)?.trim();
    return _HolderCodeParts(
      holder: plain.group(1)!.trim(),
      code: plain.group(2)!.trim(),
      rest: rest != null && rest.isNotEmpty ? rest : null,
    );
  }
  return null;
}
