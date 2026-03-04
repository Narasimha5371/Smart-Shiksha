import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/models/syllabus.dart';
import 'package:smart_shiksha/services/api_service.dart';
import 'package:smart_shiksha/services/auth_service.dart';

/// Quiz screen: pick a subject → chapter → interactive MCQ/MSQ/Numerical quiz.
class QuizScreen extends StatefulWidget {
  const QuizScreen({super.key});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  final _api = ApiService();
  List<Subject>? _subjects;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final user = context.read<AuthService>().user!;
    try {
      final subjects = await _api.getSubjects(
        curriculum: user.curriculum ?? 'CBSE',
        classGrade: user.classGrade ?? 10,
        stream: user.stream,
      );
      if (mounted) setState(() { _subjects = subjects; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Quizzes')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _subjects == null || _subjects!.isEmpty
              ? const Center(child: Text('No subjects found'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _subjects!.length,
                  itemBuilder: (context, i) {
                    final s = _subjects![i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor:
                              Theme.of(context).colorScheme.primaryContainer,
                          child: Icon(Icons.quiz_rounded,
                              color: Theme.of(context).colorScheme.primary),
                        ),
                        title: Text(s.name),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => _QuizChaptersPage(subject: s),
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

// ─── Pick chapter ────────────────────────────────────────
class _QuizChaptersPage extends StatefulWidget {
  final Subject subject;
  const _QuizChaptersPage({required this.subject});
  @override
  State<_QuizChaptersPage> createState() => _QuizChaptersPageState();
}

class _QuizChaptersPageState extends State<_QuizChaptersPage> {
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
      appBar: AppBar(title: Text('${widget.subject.name} — Quizzes')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _chapters == null || _chapters!.isEmpty
              ? const Center(child: Text('No chapters'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _chapters!.length,
                  itemBuilder: (context, i) {
                    final ch = _chapters![i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor:
                              Theme.of(context).colorScheme.secondaryContainer,
                          child: Text('${ch.order}',
                              style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Theme.of(context)
                                      .colorScheme
                                      .onSecondaryContainer)),
                        ),
                        title: Text(ch.title),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => _QuizPage(chapter: ch),
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

// ─── Interactive Quiz Page ───────────────────────────────
class _QuizPage extends StatefulWidget {
  final Chapter chapter;
  const _QuizPage({required this.chapter});
  @override
  State<_QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<_QuizPage> {
  final _api = ApiService();
  List<FlashCard> _questions = [];
  bool _loading = true;
  bool _generating = false;
  bool _submitted = false;

  // User answers: index → selected option key(s) or typed answer
  final Map<int, Set<String>> _selectedOptions = {};  // for MCQ/MSQ
  final Map<int, String> _numericalAnswers = {};       // for numerical

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final cards = await _api.getFlashcards(widget.chapter.id);
      if (mounted) setState(() { _questions = cards; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final cards = await _api.generateFlashcards(widget.chapter.id);
      if (mounted) {
        setState(() {
          _questions = cards;
          _generating = false;
          _submitted = false;
          _selectedOptions.clear();
          _numericalAnswers.clear();
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

  void _submit() {
    setState(() => _submitted = true);
  }

  void _reset() {
    setState(() {
      _submitted = false;
      _selectedOptions.clear();
      _numericalAnswers.clear();
    });
  }

  int get _score {
    int correct = 0;
    for (int i = 0; i < _questions.length; i++) {
      if (_isCorrect(i)) correct++;
    }
    return correct;
  }

  bool _isCorrect(int index) {
    final q = _questions[index];
    if (q.questionType == 'numerical') {
      final userAns = _numericalAnswers[index]?.trim() ?? '';
      return userAns.isNotEmpty && userAns == q.answer.trim();
    }
    final selected = _selectedOptions[index] ?? {};
    return selected.isNotEmpty &&
        selected.length == q.correctKeys.length &&
        selected.every((k) => q.correctKeys.contains(k));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.chapter.title),
        actions: [
          if (_questions.isNotEmpty && _submitted)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Chip(
                  avatar: Icon(Icons.check_circle, color: Colors.green.shade700, size: 18),
                  label: Text('$_score / ${_questions.length}',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: _questions.isEmpty
          ? FloatingActionButton.extended(
              onPressed: _generating ? null : _generate,
              icon: _generating
                  ? const SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.auto_awesome),
              label: Text(_generating ? 'Generating…' : 'Generate Quiz'),
            )
          : null,
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _questions.isEmpty
              ? const Center(
                  child: Text('No quiz yet.\nTap Generate Quiz to create one!',
                      textAlign: TextAlign.center))
              : Column(
                  children: [
                    // Question type legend
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                      child: Row(
                        children: [
                          _typeBadge('MCQ', Colors.blue, theme),
                          const SizedBox(width: 8),
                          _typeBadge('MSQ', Colors.orange, theme),
                          const SizedBox(width: 8),
                          _typeBadge('NUM', Colors.purple, theme),
                          const Spacer(),
                          Text('${_questions.length} questions',
                              style: theme.textTheme.bodySmall),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Questions list
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                        itemCount: _questions.length,
                        itemBuilder: (context, i) => _buildQuestion(i, theme),
                      ),
                    ),
                    // Submit / Reset bar
                    SafeArea(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            if (_submitted) ...[
                              Expanded(
                                child: FilledButton.icon(
                                  onPressed: _reset,
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Retry'),
                                ),
                              ),
                            ] else ...[
                              Expanded(
                                child: FilledButton.icon(
                                  onPressed: _submit,
                                  icon: const Icon(Icons.send_rounded),
                                  label: const Text('Submit Answers'),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _typeBadge(String label, Color color, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 11, fontWeight: FontWeight.w700, color: color)),
    );
  }

  Widget _buildQuestion(int index, ThemeData theme) {
    final q = _questions[index];
    final isCorrect = _submitted ? _isCorrect(index) : null;

    Color? cardColor;
    if (_submitted) {
      cardColor = isCorrect!
          ? Colors.green.withValues(alpha: 0.06)
          : Colors.red.withValues(alpha: 0.06);
    }

    Color typeColor;
    String typeLabel;
    switch (q.questionType) {
      case 'msq':
        typeColor = Colors.orange;
        typeLabel = 'MSQ — Select all correct';
        break;
      case 'numerical':
        typeColor = Colors.purple;
        typeLabel = 'NUMERICAL';
        break;
      default:
        typeColor = Colors.blue;
        typeLabel = 'MCQ — Single correct';
    }

    return Card(
      color: cardColor,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: _submitted
            ? BorderSide(
                color: isCorrect! ? Colors.green : Colors.red,
                width: 1.5)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: Q number + type badge
            Row(
              children: [
                CircleAvatar(
                  radius: 14,
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Text('${index + 1}',
                      style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.onPrimaryContainer)),
                ),
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: typeColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(typeLabel,
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: typeColor)),
                ),
                if (_submitted) ...[
                  const Spacer(),
                  Icon(
                    isCorrect! ? Icons.check_circle : Icons.cancel,
                    color: isCorrect ? Colors.green : Colors.red,
                    size: 20,
                  ),
                ],
              ],
            ),
            const SizedBox(height: 10),
            // Question text
            Text(q.question,
                style: const TextStyle(
                    fontSize: 15, fontWeight: FontWeight.w600, height: 1.4)),
            const SizedBox(height: 12),
            // Answer area
            if (q.questionType == 'numerical')
              _buildNumericalInput(index, q)
            else
              _buildOptions(index, q),
            // Explanation (shown after submit)
            if (_submitted && q.explanation != null && q.explanation!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest
                      .withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Explanation',
                        style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: theme.colorScheme.primary)),
                    const SizedBox(height: 4),
                    Text(q.explanation!,
                        style: TextStyle(
                            fontSize: 13,
                            color: theme.colorScheme.onSurfaceVariant,
                            height: 1.4)),
                    if (_submitted) ...[
                      const SizedBox(height: 6),
                      Text('Correct answer: ${q.answer}',
                          style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Colors.green.shade700)),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildOptions(int index, FlashCard q) {
    final options = q.options ?? [];
    final selected = _selectedOptions[index] ?? {};
    final isMsq = q.questionType == 'msq';

    return Column(
      children: options.map((opt) {
        final key = FlashCard.optionKey(opt).toUpperCase();
        final isSelected = selected.contains(key);
        final bool? isOptCorrect =
            _submitted ? q.correctKeys.contains(key) : null;

        Color? tileColor;
        if (_submitted) {
          if (isOptCorrect! && isSelected) {
            tileColor = Colors.green.withValues(alpha: 0.12);
          } else if (!isOptCorrect && isSelected) {
            tileColor = Colors.red.withValues(alpha: 0.12);
          } else if (isOptCorrect) {
            tileColor = Colors.green.withValues(alpha: 0.06);
          }
        }

        return Container(
          margin: const EdgeInsets.only(bottom: 6),
          decoration: BoxDecoration(
            color: tileColor ?? Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected && !_submitted
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.outlineVariant,
              width: isSelected && !_submitted ? 2 : 1,
            ),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(8),
            onTap: _submitted
                ? null
                : () {
                    setState(() {
                      final set = _selectedOptions[index] ?? {};
                      if (isMsq) {
                        // Toggle for MSQ
                        if (set.contains(key)) {
                          set.remove(key);
                        } else {
                          set.add(key);
                        }
                      } else {
                        // Single select for MCQ
                        set.clear();
                        set.add(key);
                      }
                      _selectedOptions[index] = set;
                    });
                  },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  if (isMsq)
                    Icon(
                      isSelected
                          ? Icons.check_box
                          : Icons.check_box_outline_blank,
                      size: 20,
                      color: _submitted
                          ? (isOptCorrect!
                              ? Colors.green
                              : (isSelected ? Colors.red : null))
                          : (isSelected
                              ? Theme.of(context).colorScheme.primary
                              : null),
                    )
                  else
                    Icon(
                      isSelected
                          ? Icons.radio_button_checked
                          : Icons.radio_button_off,
                      size: 20,
                      color: _submitted
                          ? (isOptCorrect!
                              ? Colors.green
                              : (isSelected ? Colors.red : null))
                          : (isSelected
                              ? Theme.of(context).colorScheme.primary
                              : null),
                    ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(opt,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight:
                              isSelected ? FontWeight.w600 : FontWeight.w400,
                        )),
                  ),
                  if (_submitted && isOptCorrect == true)
                    const Icon(Icons.check, color: Colors.green, size: 18),
                  if (_submitted && isOptCorrect == false && isSelected)
                    const Icon(Icons.close, color: Colors.red, size: 18),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildNumericalInput(int index, FlashCard q) {
    final bool? isCorrect = _submitted ? _isCorrect(index) : null;
    return TextField(
      enabled: !_submitted,
      keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
      decoration: InputDecoration(
        hintText: 'Type your numerical answer…',
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        filled: _submitted,
        fillColor: _submitted
            ? (isCorrect!
                ? Colors.green.withValues(alpha: 0.08)
                : Colors.red.withValues(alpha: 0.08))
            : null,
        suffixIcon: _submitted
            ? Icon(isCorrect! ? Icons.check_circle : Icons.cancel,
                color: isCorrect ? Colors.green : Colors.red)
            : null,
      ),
      onChanged: (v) => _numericalAnswers[index] = v,
    );
  }
}
