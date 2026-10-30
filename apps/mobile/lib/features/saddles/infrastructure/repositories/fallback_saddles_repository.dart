import 'package:mobile_domain/src/saddles/saddle_list_item.dart';
import 'package:mobile_domain/src/saddles/saddles_repository.dart';

class FallbackSaddlesRepository implements SaddlesRepository {
  @override
  Future<List<SaddleListItem>> listSaddles({
    bool includeDeleted = false,
  }) async {
    return const <SaddleListItem>[];
  }

  @override
  Future<SaddleListItem> getSaddleById(String saddleId) async {
    throw Exception('SaddlesModule no inyectado');
  }

  @override
  Future<SaddleListItem> createSaddle({
    required String code,
    String? name,
    bool isAvailable = true,
    String? notes,
  }) async {
    throw Exception('SaddlesModule no inyectado');
  }

  @override
  Future<SaddleListItem> updateSaddle({
    required String saddleId,
    String? code,
    String? name,
    bool? isAvailable,
    String? notes,
  }) async {
    throw Exception('SaddlesModule no inyectado');
  }

  @override
  Future<SaddleListItem> deleteSaddle(String saddleId) async {
    throw Exception('SaddlesModule no inyectado');
  }

  @override
  Future<SaddleListItem> restoreSaddle(String saddleId) async {
    throw Exception('SaddlesModule no inyectado');
  }
}
