/// Distribuye cards en columnas que llenan el ancho disponible.
class BoardGridLayout {
  const BoardGridLayout({
    required this.columnCount,
    required this.baseCardWidth,
  });

  final int columnCount;
  final double baseCardWidth;

  double cardWidthFor(int index, int itemCount, double maxWidth) {
    final remainder = itemCount % columnCount;
    if (remainder == 1 && index == itemCount - 1) {
      return maxWidth;
    }
    return baseCardWidth;
  }

  static BoardGridLayout forWidth({
    required double maxWidth,
    required int itemCount,
    double minCardWidth = 140,
    double spacing = 8,
  }) {
    final columnCount = ((maxWidth + spacing) / (minCardWidth + spacing))
        .floor()
        .clamp(1, itemCount > 0 ? itemCount : 1);
    final baseCardWidth =
        (maxWidth - spacing * (columnCount - 1)) / columnCount;

    return BoardGridLayout(
      columnCount: columnCount,
      baseCardWidth: baseCardWidth,
    );
  }
}
