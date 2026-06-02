import 'package:mobile_domain/src/saddles/saddle_list_item.dart';

abstract class SaddlesRepository {
  Future<List<SaddleListItem>> listSaddles({bool includeDeleted = false});

  Future<SaddleListItem> getSaddleById(String saddleId);

  Future<SaddleListItem> createSaddle({
    required String code,
    String? name,
    bool isAvailable = true,
    String? notes,
  });

  Future<SaddleListItem> updateSaddle({
    required String saddleId,
    String? code,
    String? name,
    bool? isAvailable,
    String? notes,
  });

  Future<SaddleListItem> deleteSaddle(String saddleId);

  Future<SaddleListItem> restoreSaddle(String saddleId);
}
