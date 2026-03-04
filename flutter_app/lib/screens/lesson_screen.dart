import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:smart_shiksha/models/lesson.dart';
import 'package:smart_shiksha/l10n/app_localizations.dart';

class LessonScreen extends StatelessWidget {
  final Lesson lesson;

  const LessonScreen({super.key, required this.lesson});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(title: Text(lesson.topic)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Markdown content ──
              MarkdownBody(
                data: lesson.content,
                selectable: true,
                styleSheet: MarkdownStyleSheet(
                  h2: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  h3: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                  p: const TextStyle(fontSize: 16, height: 1.7),
                  listBullet: const TextStyle(fontSize: 16, height: 1.6),
                  blockquoteDecoration: BoxDecoration(
                    color: Colors.amber.shade50,
                    border: Border(
                      left: BorderSide(color: Colors.amber.shade700, width: 4),
                    ),
                  ),
                ),
              ),

              // ── Sources ──
              if (lesson.sources.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Divider(),
                Text(
                  l10n.sourcesHeading,
                  style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                ),
                const SizedBox(height: 6),
                ...lesson.sources.map(
                  (url) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: InkWell(
                      onTap: () => _openUrl(url),
                      child: Text(
                        url,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.primary,
                          fontSize: 13,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _openUrl(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
