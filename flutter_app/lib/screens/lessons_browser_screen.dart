import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/models/syllabus.dart';
import 'package:smart_shiksha/services/api_service.dart';
import 'package:smart_shiksha/services/auth_service.dart';

/// Browse subjects → chapters → generated lessons.
class LessonsBrowserScreen extends StatefulWidget {
  const LessonsBrowserScreen({super.key});

  @override
  State<LessonsBrowserScreen> createState() => _LessonsBrowserScreenState();
}

class _LessonsBrowserScreenState extends State<LessonsBrowserScreen> {
  final _api = ApiService();
  List<Subject>? _subjects;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSubjects();
  }

  Future<void> _loadSubjects() async {
    final user = context.read<AuthService>().user!;
    try {
      final subjects = await _api.getSubjects(
        curriculum: user.curriculum ?? 'CBSE',
        classGrade: user.classGrade ?? 10,
        stream: user.stream,
      );
      if (mounted) setState(() { _subjects = subjects; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Lessons')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _subjects == null || _subjects!.isEmpty
                  ? const Center(child: Text('No subjects found'))
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _subjects!.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, i) {
                        final s = _subjects![i];
                        return _SubjectCard(
                          subject: s,
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => _ChaptersPage(subject: s),
                            ),
                          ),
                        );
                      },
                    ),
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final Subject subject;
  final VoidCallback onTap;
  const _SubjectCard({required this.subject, required this.onTap});

  IconData _icon() {
    final lower = subject.name.toLowerCase();
    if (lower.contains('math')) return Icons.calculate_rounded;
    if (lower.contains('physics')) return Icons.science_rounded;
    if (lower.contains('chemistry')) return Icons.biotech_rounded;
    if (lower.contains('biology')) return Icons.spa_rounded;
    if (lower.contains('english')) return Icons.menu_book_rounded;
    if (lower.contains('hindi')) return Icons.translate_rounded;
    if (lower.contains('history')) return Icons.account_balance_rounded;
    if (lower.contains('geography')) return Icons.public_rounded;
    if (lower.contains('economics')) return Icons.trending_up_rounded;
    if (lower.contains('social')) return Icons.groups_rounded;
    if (lower.contains('account')) return Icons.receipt_long_rounded;
    if (lower.contains('business')) return Icons.business_center_rounded;
    if (lower.contains('political')) return Icons.gavel_rounded;
    return Icons.book_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.primaryContainer,
          child: Icon(_icon(), color: theme.colorScheme.primary),
        ),
        title: Text(subject.name, style: const TextStyle(fontWeight: FontWeight.w600)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

// ── Chapters list ──────────────────────────────────────────
class _ChaptersPage extends StatefulWidget {
  final Subject subject;
  const _ChaptersPage({required this.subject});
  @override
  State<_ChaptersPage> createState() => _ChaptersPageState();
}

class _ChaptersPageState extends State<_ChaptersPage> {
  final _api = ApiService();
  List<Chapter>? _chapters;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final chapters = await _api.getChapters(widget.subject.id);
      if (mounted) setState(() { _chapters = chapters; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.subject.name)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _chapters == null || _chapters!.isEmpty
              ? const Center(child: Text('No chapters available'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _chapters!.length,
                  itemBuilder: (context, i) {
                    final ch = _chapters![i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor:
                              Theme.of(context).colorScheme.secondaryContainer,
                          child: Text('${ch.order}',
                              style: TextStyle(
                                  color: Theme.of(context)
                                      .colorScheme
                                      .onSecondaryContainer,
                                  fontWeight: FontWeight.bold)),
                        ),
                        title: Text(ch.title),
                        subtitle: ch.description != null
                            ? Text(ch.description!,
                                maxLines: 2, overflow: TextOverflow.ellipsis)
                            : null,
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                _ChapterLessonsPage(chapter: ch),
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

// ── Generated lessons inside a chapter ─────────────────────
class _ChapterLessonsPage extends StatefulWidget {
  final Chapter chapter;
  const _ChapterLessonsPage({required this.chapter});
  @override
  State<_ChapterLessonsPage> createState() => _ChapterLessonsPageState();
}

class _ChapterLessonsPageState extends State<_ChapterLessonsPage> {
  final _api = ApiService();
  List<GeneratedLesson> _lessons = [];
  bool _loading = true;
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final lessons = await _api.getGeneratedLessons(widget.chapter.id);
      if (mounted) setState(() { _lessons = lessons; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final lesson = await _api.generateLesson(widget.chapter.id);
      if (mounted) {
        setState(() {
          _lessons.add(lesson);
          _generating = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _generating = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.chapter.title)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _generating ? null : _generate,
        icon: _generating
            ? const SizedBox(
                width: 20, height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : const Icon(Icons.auto_awesome),
        label: Text(_generating ? 'Generating…' : 'Generate Lesson'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _lessons.isEmpty
              ? const Center(
                  child: Text('No lessons yet.\nTap Generate to create one!',
                      textAlign: TextAlign.center))
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                  itemCount: _lessons.length,
                  itemBuilder: (context, i) {
                    final lesson = _lessons[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        title: Text(lesson.title,
                            style:
                                const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Text(
                            'Language: ${lesson.languageCode} • Order: ${lesson.order}'),
                        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                _LessonDetailPage(lesson: lesson),
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

// ── Full lesson markdown view ──────────────────────────────
class _LessonDetailPage extends StatelessWidget {
  final GeneratedLesson lesson;
  const _LessonDetailPage({required this.lesson});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(lesson.title)),
      body: Markdown(
        data: lesson.contentMarkdown,
        padding: const EdgeInsets.all(16),
        selectable: true,
        styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
          h1: Theme.of(context).textTheme.headlineSmall,
          h2: Theme.of(context).textTheme.titleLarge,
          p: Theme.of(context).textTheme.bodyLarge,
        ),
      ),
    );
  }
}
