import '../models/reservation_detail.dart';
import '../models/reservation_list_item.dart';
import '../models/reservation_status.dart';

abstract class ReservationsRepository {
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  });

  Future<ReservationDetail> getReservationById(String reservationId);

  Future<List<ReservationListItem>> getCachedReservations();

  Future<ReservationDetail?> getCachedReservationDetail(String reservationId);
}
