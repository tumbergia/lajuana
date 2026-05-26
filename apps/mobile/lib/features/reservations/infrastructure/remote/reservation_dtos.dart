class ReservationListItemDto {
  ReservationListItemDto({
    this.id,
    this.code,
    this.status,
    this.participantCount,
    this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.experienceId,
    this.experienceName,
    this.scheduleId,
    this.requestedDate,
    this.scheduledDate,
    this.startTime,
    this.expectedParticipantsCount,
    this.participantsCompletedCount,
    this.participantFormStatus,
    this.channel,
    this.version,
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
  });

  final String? id;
  final String? code;
  final String? status;
  final int? participantCount;
  final String? paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final String? experienceId;
  final String? experienceName;
  final String? scheduleId;
  final String? requestedDate;
  final String? scheduledDate;
  final String? startTime;
  final int? expectedParticipantsCount;
  final int? participantsCompletedCount;
  final String? participantFormStatus;
  final String? channel;
  final int? version;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final DateTime? deletedAt;

  factory ReservationListItemDto.fromJson(Map<String, dynamic> json) {
    return ReservationListItemDto(
      id: json['id'] as String?,
      code: json['code'] as String?,
      status: json['status'] as String?,
      participantCount: json['participant_count'] as int?,
      paymentStatus: json['payment_status'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      experienceId: json['experience_id'] as String?,
      experienceName: json['experience_name'] as String?,
      scheduleId: json['schedule_id'] as String?,
      requestedDate: json['requested_date'] as String?,
      scheduledDate: json['scheduled_date'] as String?,
      startTime: json['start_time'] as String?,
      expectedParticipantsCount: json['expected_participants_count'] as int?,
      participantsCompletedCount: json['participants_completed_count'] as int?,
      participantFormStatus: json['participant_form_status'] as String?,
      channel: json['channel'] as String?,
      version: json['version'] as int?,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String).toUtc(),
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String).toUtc(),
      deletedAt: json['deleted_at'] == null
          ? null
          : DateTime.parse(json['deleted_at'] as String).toUtc(),
    );
  }
}

class ReservationDetailDto {
  ReservationDetailDto({
    this.id,
    this.code,
    this.experienceId,
    this.scheduleId,
    this.channel,
    this.status,
    this.participantCount,
    this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.requestedDate,
    this.quotedTotalAmount,
    this.currency,
    this.expectedParticipantsCount,
    this.participantsCompletedCount,
    this.participantFormStatus,
    this.formUrl,
    this.confirmedAt,
    this.cancelledAt,
    this.completedAt,
    this.version,
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
  });

  final String? id;
  final String? code;
  final String? experienceId;
  final String? scheduleId;
  final String? channel;
  final String? status;
  final int? participantCount;
  final String? paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final String? requestedDate;
  final String? quotedTotalAmount;
  final String? currency;
  final int? expectedParticipantsCount;
  final int? participantsCompletedCount;
  final String? participantFormStatus;
  final String? formUrl;
  final DateTime? confirmedAt;
  final DateTime? cancelledAt;
  final DateTime? completedAt;
  final int? version;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final DateTime? deletedAt;

  factory ReservationDetailDto.fromJson(Map<String, dynamic> json) {
    return ReservationDetailDto(
      id: json['id'] as String?,
      code: json['code'] as String?,
      experienceId: json['experience_id'] as String?,
      scheduleId: json['schedule_id'] as String?,
      channel: json['channel'] as String?,
      status: json['status'] as String?,
      participantCount: json['participant_count'] as int?,
      paymentStatus: json['payment_status'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      requestedDate: json['requested_date'] as String?,
      quotedTotalAmount: json['quoted_total_amount'] as String?,
      currency: json['currency'] as String?,
      expectedParticipantsCount: json['expected_participants_count'] as int?,
      participantsCompletedCount: json['participants_completed_count'] as int?,
      participantFormStatus: json['participant_form_status'] as String?,
      formUrl: json['form_url'] as String?,
      confirmedAt: json['confirmed_at'] == null
          ? null
          : DateTime.parse(json['confirmed_at'] as String).toUtc(),
      cancelledAt: json['cancelled_at'] == null
          ? null
          : DateTime.parse(json['cancelled_at'] as String).toUtc(),
      completedAt: json['completed_at'] == null
          ? null
          : DateTime.parse(json['completed_at'] as String).toUtc(),
      version: json['version'] as int?,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String).toUtc(),
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String).toUtc(),
      deletedAt: json['deleted_at'] == null
          ? null
          : DateTime.parse(json['deleted_at'] as String).toUtc(),
    );
  }
}
