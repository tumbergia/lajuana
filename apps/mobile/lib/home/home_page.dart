import 'package:flutter/material.dart';
import '../app/widgets/app_bottom_nav.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_card.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_text_field.dart';
import '../app/widgets/app_top_bar.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return AppScaffold(
      appBar: const AppTopBar(
        logoAssetPath: 'assets/branding/lajuana.svg',
        title: 'LA JUANA',
      ),
      bottomNavigationBar: AppBottomNav(
        current: AppNavItem.clientes,
        onTap: (item) {},
      ),
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Operational Database',
            style: theme.textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'People',
            style: theme.textTheme.displaySmall?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 24),
          AppButton(
            label: 'Register Participant',
            icon: Icons.add,
            variant: AppButtonVariant.primary,
            expanded: true,
            onPressed: () {},
          ),
          const SizedBox(height: 16),
          const AppTextField(
            label: 'Search',
            hintText: 'SEARCH PARTICIPANTS...',
            variant: AppTextFieldVariant.underlined,
            suffix: Icon(Icons.manage_search_rounded),
          ),
          const SizedBox(height: 24),
          AppCard(
            accentColor: Colors.white,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Elena Rodriguez',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'EXP: INTERMEDIATE • 68KG',
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                    letterSpacing: 0.6,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
