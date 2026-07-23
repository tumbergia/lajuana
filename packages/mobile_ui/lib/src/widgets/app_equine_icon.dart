import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Brand horse mark used wherever equines are represented (replaces the chess knight).
class AppEquineIcon extends StatelessWidget {
  const AppEquineIcon({
    super.key,
    this.size = 24,
    this.color,
  });

  static const String assetPath = 'assets/icons/equine.svg';

  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final resolved =
        color ?? IconTheme.of(context).color ?? Theme.of(context).iconTheme.color;

    return SvgPicture.asset(
      assetPath,
      package: 'mobile_ui',
      width: size,
      height: size,
      fit: BoxFit.contain,
      colorFilter: resolved == null
          ? null
          : ColorFilter.mode(resolved, BlendMode.srcIn),
    );
  }
}
