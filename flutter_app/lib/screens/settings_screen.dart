import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/core/constants.dart';
import 'package:smart_shiksha/services/db_service.dart';
import 'package:smart_shiksha/services/localization_service.dart';
import 'package:smart_shiksha/l10n/app_localizations.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final locService = context.watch<LocalizationService>();

    return Scaffold(
      appBar: AppBar(title: Text(l10n.settings)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Language preference ──
          Text(
            l10n.selectLanguage,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          ...AppConstants.supportedLanguages.entries.map((entry) {
            final selected = locService.languageCode == entry.key;
            return Card(
              color: selected
                  ? Theme.of(context).colorScheme.primaryContainer
                  : null,
              child: ListTile(
                title: Text(entry.value),
                trailing: selected
                    ? Icon(
                        Icons.check_circle,
                        color: Theme.of(context).colorScheme.primary,
                      )
                    : null,
                onTap: () => locService.setLanguage(entry.key),
              ),
            );
          }),

          const SizedBox(height: 32),

          // ── Clear cache ──
          OutlinedButton.icon(
            onPressed: () async {
              await DbService().clearCache();
              if (context.mounted) {
                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(const SnackBar(content: Text('Cache cleared')));
              }
            },
            icon: const Icon(Icons.delete_outline),
            label: const Text('Clear Offline Cache'),
          ),
        ],
      ),
    );
  }
}
