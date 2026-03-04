import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/core/constants.dart';
import 'package:smart_shiksha/models/lesson.dart';
import 'package:smart_shiksha/services/api_service.dart';
import 'package:smart_shiksha/services/db_service.dart';
import 'package:smart_shiksha/services/localization_service.dart';
import 'package:smart_shiksha/screens/lesson_screen.dart';
import 'package:smart_shiksha/screens/settings_screen.dart';
import 'package:smart_shiksha/l10n/app_localizations.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _controller = TextEditingController();
  final _apiService = ApiService();
  final _dbService = DbService();

  bool _loading = false;
  String? _error;
  List<Lesson> _cachedLessons = [];

  @override
  void initState() {
    super.initState();
    _loadCachedLessons();
  }

  Future<void> _loadCachedLessons() async {
    try {
      final lessons = await _dbService.getCachedLessons();
      if (mounted) setState(() => _cachedLessons = lessons);
    } catch (_) {}
  }

  Future<void> _askQuestion() async {
    final question = _controller.text.trim();
    if (question.isEmpty) return;

    final lang = context.read<LocalizationService>().languageCode;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final lesson = await _apiService.askQuestion(question, lang);

      // Cache offline
      await _dbService.cacheLesson(lesson);
      await _loadCachedLessons();

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => LessonScreen(lesson: lesson)),
        );
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final locService = context.watch<LocalizationService>();

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        actions: [
          // Language dropdown
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: locService.languageCode,
                dropdownColor: Theme.of(context).colorScheme.primaryContainer,
                iconEnabledColor: Colors.white,
                style: const TextStyle(color: Colors.white, fontSize: 14),
                items: AppConstants.supportedLanguages.entries
                    .map(
                      (e) => DropdownMenuItem(
                        value: e.key,
                        child: Text(
                          e.value,
                          style: const TextStyle(color: Colors.black87),
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (code) {
                  if (code != null) locService.setLanguage(code);
                },
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: l10n.settings,
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Tagline ──
              Text(
                l10n.tagline,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                      fontStyle: FontStyle.italic,
                    ),
              ),
              const SizedBox(height: 20),

              // ── Question Input ──
              Text(
                l10n.askHeading,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _controller,
                maxLines: 3,
                maxLength: 1000,
                textInputAction: TextInputAction.done,
                decoration: InputDecoration(hintText: l10n.questionPlaceholder),
                onSubmitted: (_) => _askQuestion(),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: _loading ? null : _askQuestion,
                child: _loading
                    ? Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Text(l10n.loading),
                        ],
                      )
                    : Text(l10n.askButton),
              ),

              // ── Error ──
              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _error!,
                    style: TextStyle(color: Colors.red.shade800),
                  ),
                ),
              ],

              const SizedBox(height: 24),

              // ── Saved / Cached Lessons ──
              Text(
                l10n.savedHeading,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Expanded(
                child: _cachedLessons.isEmpty
                    ? Center(
                        child: Text(
                          l10n.noSavedLessons,
                          style: TextStyle(
                            color: Colors.grey[500],
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _cachedLessons.length,
                        itemBuilder: (ctx, i) {
                          final lesson = _cachedLessons[i];
                          return Card(
                            child: ListTile(
                              title: Text(
                                lesson.topic,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              subtitle: Text(
                                '${lesson.languageCode.toUpperCase()} · ${lesson.createdAt?.toLocal().toString().split(' ').first ?? ''}',
                                style: TextStyle(
                                  color: Colors.grey[600],
                                  fontSize: 12,
                                ),
                              ),
                              trailing: const Icon(
                                Icons.chevron_right,
                                size: 20,
                              ),
                              onTap: () => Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => LessonScreen(lesson: lesson),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
