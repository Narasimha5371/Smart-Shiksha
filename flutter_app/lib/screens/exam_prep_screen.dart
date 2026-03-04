import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/models/syllabus.dart';
import 'package:smart_shiksha/services/api_service.dart';
import 'package:smart_shiksha/services/auth_service.dart';

/// Exam Prep: context-aware by class.
///   Class 8-9  → Final Exam practice
///   Class 10   → Board Exam practice
///   Class 11-12 → Competitive Exams (JEE / NEET)
class ExamPrepScreen extends StatefulWidget {
  const ExamPrepScreen({super.key});

  @override
  State<ExamPrepScreen> createState() => _ExamPrepScreenState();
}

class _ExamPrepScreenState extends State<ExamPrepScreen> {
  final _api = ApiService();
  List<CompetitiveExam> _exams = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final user = context.read<AuthService>().user;
      final grade = user?.classGrade;
      final exams = await _api.getExams(classGrade: grade);
      if (mounted) {
        setState(() {
          _exams = exams;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// Contextual heading based on class.
  String _examCategory(int? grade) {
    if (grade != null && grade <= 9) return 'Final Exam Practice';
    if (grade == 10) return 'Board Exam Preparation';
    return 'Competitive Exam Preparation';
  }

  String _examSubtitle(int? grade) {
    if (grade != null && grade <= 9) {
      return 'Practice for your Class $grade annual exams';
    }
    if (grade == 10) {
      return 'Prepare for your Class 10 Board exams';
    }
    return 'JEE, NEET & other entrance exams';
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthService>().user;
    final grade = user?.classGrade;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(_examCategory(grade))),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _exams.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.school_rounded,
                            size: 64,
                            color: theme.colorScheme.onSurfaceVariant),
                        const SizedBox(height: 16),
                        Text('No exams available for Class ${grade ?? "?"}',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.titleMedium),
                      ],
                    ),
                  ),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                      child: Text(_examSubtitle(grade),
                          style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant)),
                    ),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _exams.length,
                        itemBuilder: (context, i) {
                          final exam = _exams[i];
                          return _ExamCard(
                            exam: exam,
                            classGrade: grade,
                            onTap: () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => _MockTestsPage(exam: exam),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
    );
  }
}

class _ExamCard extends StatelessWidget {
  final CompetitiveExam exam;
  final int? classGrade;
  final VoidCallback onTap;
  const _ExamCard({required this.exam, required this.onTap, this.classGrade});

  Color _color() {
    if (exam.name.contains('NEET')) return Colors.green;
    if (exam.name.contains('Advanced')) return Colors.deepOrange;
    if (exam.name.contains('Board')) return Colors.indigo;
    if (exam.name.contains('Final')) return Colors.teal;
    return Colors.blue;
  }

  IconData _icon() {
    if (exam.name.contains('NEET')) return Icons.local_hospital_rounded;
    if (exam.name.contains('Board')) return Icons.school_rounded;
    if (exam.name.contains('Final')) return Icons.assignment_rounded;
    return Icons.engineering_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final c = _color();
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [c.withValues(alpha: 0.12), c.withValues(alpha: 0.04)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: c.withValues(alpha: 0.2),
                child: Icon(_icon(), color: c, size: 28),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(exam.name,
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                            color: c)),
                    if (exam.description != null) ...[
                      const SizedBox(height: 4),
                      Text(exam.description!,
                          style: TextStyle(
                              fontSize: 13,
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant)),
                    ],
                    if (exam.subjects.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        children: exam.subjects
                            .map((s) => Chip(
                                  label: Text(s,
                                      style: const TextStyle(fontSize: 11)),
                                  visualDensity: VisualDensity.compact,
                                  materialTapTargetSize:
                                      MaterialTapTargetSize.shrinkWrap,
                                ))
                            .toList(),
                      ),
                    ],
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Mock tests list ────────────────────────────────────────
class _MockTestsPage extends StatefulWidget {
  final CompetitiveExam exam;
  const _MockTestsPage({required this.exam});
  @override
  State<_MockTestsPage> createState() => _MockTestsPageState();
}

class _MockTestsPageState extends State<_MockTestsPage> {
  final _api = ApiService();
  List<MockTest> _tests = [];
  bool _loading = true;
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final tests = await _api.getMockTests(widget.exam.id);
      if (mounted) {
        setState(() {
          _tests = tests;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final test = await _api.generateMockTest(widget.exam.id);
      if (mounted) {
        setState(() {
          _tests.add(test);
          _generating = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _generating = false);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Failed: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.exam.name)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _generating ? null : _generate,
        icon: _generating
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: Colors.white))
            : const Icon(Icons.auto_awesome),
        label: Text(_generating ? 'Generating…' : 'New Mock Test'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _tests.isEmpty
              ? const Center(
                  child: Text(
                      'No mock tests yet.\nTap the button to generate one!',
                      textAlign: TextAlign.center))
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                  itemCount: _tests.length,
                  itemBuilder: (context, i) {
                    final test = _tests[i];
                    final qCount = test.questionsJson?.length ?? 0;
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor:
                              Theme.of(context).colorScheme.primaryContainer,
                          child: Text('${i + 1}',
                              style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Theme.of(context)
                                      .colorScheme
                                      .onPrimaryContainer)),
                        ),
                        title: Text(test.title),
                        subtitle: Text(
                            '$qCount questions • ${test.durationMinutes} min • ${test.totalMarks} marks'),
                        trailing: const Icon(Icons.play_arrow_rounded),
                        onTap: () {
                          if (test.questionsJson == null ||
                              test.questionsJson!.isEmpty) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text('No questions in this test')),
                            );
                            return;
                          }
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => _TakeTestPage(test: test),
                            ),
                          );
                        },
                      ),
                    );
                  },
                ),
    );
  }
}

// ── Take a mock test (MCQ) ─────────────────────────────────
class _TakeTestPage extends StatefulWidget {
  final MockTest test;
  const _TakeTestPage({required this.test});
  @override
  State<_TakeTestPage> createState() => _TakeTestPageState();
}

class _TakeTestPageState extends State<_TakeTestPage> {
  late List<dynamic> _questions;
  final Map<int, String> _answers = {}; // questionIndex → chosen key (A/B/C/D)
  bool _submitted = false;
  int _score = 0;

  @override
  void initState() {
    super.initState();
    _questions = widget.test.questionsJson ?? [];
  }

  /// Extract question text – backend may use "q" or "question".
  String _qText(Map<String, dynamic> q) =>
      (q['q'] ?? q['question'] ?? '') as String;

  /// Extract option keys & values from either Map or List format.
  /// Returns list of (key, text) pairs, e.g. [("A", "Option text"), …]
  List<MapEntry<String, String>> _optionEntries(Map<String, dynamic> q) {
    final raw = q['options'];
    if (raw is Map) {
      // Backend format: {"A":"…", "B":"…", "C":"…", "D":"…"}
      final keys = ['A', 'B', 'C', 'D'];
      return keys
          .where((k) => raw.containsKey(k))
          .map((k) => MapEntry(k, raw[k].toString()))
          .toList();
    }
    if (raw is List) {
      // Fallback list format
      const labels = ['A', 'B', 'C', 'D', 'E', 'F'];
      return List.generate(
        raw.length,
        (i) => MapEntry(
            i < labels.length ? labels[i] : '${i + 1}', raw[i].toString()),
      );
    }
    return [];
  }

  /// Extract the correct answer key (e.g. "A").
  String _correctKey(Map<String, dynamic> q) {
    final ans = q['answer'] ?? q['correct'] ?? '';
    if (ans is int) {
      const labels = ['A', 'B', 'C', 'D', 'E', 'F'];
      return ans < labels.length ? labels[ans] : '';
    }
    return ans.toString().trim().toUpperCase();
  }

  void _submit() {
    int score = 0;
    for (int i = 0; i < _questions.length; i++) {
      final q = _questions[i] as Map<String, dynamic>;
      final correct = _correctKey(q);
      final chosen = _answers[i];
      if (chosen == correct) {
        score += 4;
      } else if (chosen != null) {
        score -= 1; // Negative marking
      }
    }
    setState(() {
      _submitted = true;
      _score = score;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.test.title),
        actions: [
          if (!_submitted)
            TextButton(
              onPressed: _submit,
              child: const Text('Submit',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ),
        ],
      ),
      body: _submitted
          ? _buildResults(theme)
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _questions.length,
              itemBuilder: (context, i) {
                final q = _questions[i] as Map<String, dynamic>;
                final entries = _optionEntries(q);
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Q${i + 1}. ${_qText(q)}',
                            style: const TextStyle(
                                fontWeight: FontWeight.w600, fontSize: 15)),
                        const SizedBox(height: 12),
                        ...entries.map((e) {
                          return RadioListTile<String>(
                            value: e.key,
                            groupValue: _answers[i],
                            title: Text('${e.key}. ${e.value}'),
                            dense: true,
                            onChanged: (v) =>
                                setState(() => _answers[i] = v!),
                          );
                        }),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Widget _buildResults(ThemeData theme) {
    final total = _questions.length * 4;
    final pct = total > 0 ? (_score / total * 100).clamp(0, 100) : 0;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              pct >= 60
                  ? Icons.emoji_events_rounded
                  : Icons.sentiment_neutral_rounded,
              size: 80,
              color:
                  pct >= 60 ? Colors.amber : theme.colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text('Your Score',
                style: theme.textTheme.titleMedium
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            Text('$_score / $total',
                style: theme.textTheme.displaySmall
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('${pct.toStringAsFixed(1)}%',
                style: theme.textTheme.headlineSmall
                    ?.copyWith(color: pct >= 60 ? Colors.green : Colors.red)),
            const SizedBox(height: 8),
            Text(
              'Correct: +4 marks  |  Wrong: -1 mark  |  Unattempted: 0',
              style: theme.textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            // Review answers
            Expanded(
              child: ListView.builder(
                itemCount: _questions.length,
                itemBuilder: (context, i) {
                  final q = _questions[i] as Map<String, dynamic>;
                  final entries = _optionEntries(q);
                  final correctKey = _correctKey(q);
                  final chosenKey = _answers[i];
                  final isCorrect = chosenKey == correctKey;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    color: chosenKey == null
                        ? null
                        : isCorrect
                            ? Colors.green.withValues(alpha: 0.08)
                            : Colors.red.withValues(alpha: 0.08),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Q${i + 1}. ${_qText(q)}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          ...entries.map((e) {
                            final isOCorrect = e.key == correctKey;
                            final isOChosen = e.key == chosenKey;
                            return Container(
                              margin: const EdgeInsets.only(bottom: 4),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(8),
                                color: isOCorrect
                                    ? Colors.green.withValues(alpha: 0.15)
                                    : isOChosen
                                        ? Colors.red.withValues(alpha: 0.15)
                                        : null,
                                border: isOCorrect
                                    ? Border.all(color: Colors.green)
                                    : isOChosen
                                        ? Border.all(color: Colors.red)
                                        : null,
                              ),
                              child: Row(
                                children: [
                                  if (isOCorrect)
                                    const Icon(Icons.check_circle,
                                        color: Colors.green, size: 18)
                                  else if (isOChosen)
                                    const Icon(Icons.cancel,
                                        color: Colors.red, size: 18)
                                  else
                                    const SizedBox(width: 18),
                                  const SizedBox(width: 8),
                                  Expanded(
                                      child: Text('${e.key}. ${e.value}')),
                                ],
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
