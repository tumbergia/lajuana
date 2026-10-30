// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentInstructionsSchema`.

class PaymentInstructions {
  final bool manualTransferEnabled;
  final String accountBank;
  final String accountType;
  final String accountNumber;
  final String accountHolderName;
  final String accountHolderId;
  final String transferNote;
  final bool boldEnabled;
  final String? boldCheckoutUrl;
  final double boldSurchargePercent;
  final String boldNote;

  const PaymentInstructions({
    required this.manualTransferEnabled,
    required this.accountBank,
    required this.accountType,
    required this.accountNumber,
    required this.accountHolderName,
    required this.accountHolderId,
    required this.transferNote,
    required this.boldEnabled,
    this.boldCheckoutUrl,
    required this.boldSurchargePercent,
    required this.boldNote,
  });

  factory PaymentInstructions.fromJson(Map<String, dynamic> json) {
    return PaymentInstructions(
      manualTransferEnabled: json['manual_transfer_enabled'] as bool,
      accountBank: json['account_bank'] as String,
      accountType: json['account_type'] as String,
      accountNumber: json['account_number'] as String,
      accountHolderName: json['account_holder_name'] as String,
      accountHolderId: json['account_holder_id'] as String,
      transferNote: json['transfer_note'] as String,
      boldEnabled: json['bold_enabled'] as bool,
      boldCheckoutUrl: json['bold_checkout_url'] as String?,
      boldSurchargePercent: (json['bold_surcharge_percent'] as num).toDouble(),
      boldNote: json['bold_note'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'manual_transfer_enabled': manualTransferEnabled,
    'account_bank': accountBank,
    'account_type': accountType,
    'account_number': accountNumber,
    'account_holder_name': accountHolderName,
    'account_holder_id': accountHolderId,
    'transfer_note': transferNote,
    'bold_enabled': boldEnabled,
    'bold_checkout_url': boldCheckoutUrl,
    'bold_surcharge_percent': boldSurchargePercent,
    'bold_note': boldNote,
  };
}
