import 'package:mobile_domain/src/saddles/saddle_list_item.dart';
import 'package:mobile/features/saddles/presentation/models/saddle_view_models.dart';

/// Domain -> ViewModel: SaddleListItem -> SaddleRecord
SaddleRecord listItemToRecord(SaddleListItem item) {
  return SaddleRecord(
    id: item.id,
    code: item.code,
    name: item.name ?? 'Sin nombre',
    isAvailable: item.isAvailable,
    notes: item.notes,
    isDeleted: item.isDeleted,
  );
}
