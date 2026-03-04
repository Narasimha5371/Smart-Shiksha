import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/services/auth_service.dart';
import 'package:smart_shiksha/services/api_service.dart';
import 'package:smart_shiksha/services/theme_service.dart';
import 'package:smart_shiksha/services/localization_service.dart';
import 'package:smart_shiksha/core/constants.dart';

/// Profile screen: user info, change class, subject stats, settings, logout.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _api = ApiService();
  List<Map<String, dynamic>> _stats = [];
  bool _loadingStats = true;
  List<String> _curricula = [];

  @override
  void initState() {
    super.initState();
    _loadStats();
    _loadCurricula();
  }

  Future<void> _loadCurricula() async {
    try {
      final curricula = await _api.getCurricula();
      if (mounted) setState(() => _curricula = curricula);
    } catch (_) {}
  }

  Future<void> _loadStats() async {
    try {
      final stats = await _api.getSubjectStats();
      if (mounted) {
        setState(() {
          _stats = stats;
          _loadingStats = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingStats = false);
    }
  }

  String _formatTime(int seconds) {
    if (seconds < 60) return '${seconds}s';
    if (seconds < 3600) return '${(seconds / 60).round()}m';
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    return '${h}h ${m}m';
  }

  Future<void> _showEditClassDialog() async {
    final auth = context.read<AuthService>();
    final user = auth.user!;

    // Ensure the user's current curriculum is in the list
    final curricula = List<String>.from(_curricula);
    final userCurriculum = user.curriculum ?? 'CBSE';
    if (!curricula.contains(userCurriculum)) {
      curricula.insert(0, userCurriculum);
    }

    String curriculum = userCurriculum;
    int classGrade = user.classGrade ?? 10;
    String? stream = user.stream;

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            final needsStream = classGrade >= 11;
            return AlertDialog(
              title: const Text('Change Class'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Curriculum
                    const Text('Board / Curriculum',
                        style: TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      initialValue: curriculum,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      isExpanded: true,
                      items: curricula
                          .map(
                              (c) => DropdownMenuItem(value: c, child: Text(c)))
                          .toList(),
                      onChanged: (v) {
                        if (v != null) setDialogState(() => curriculum = v);
                      },
                    ),
                    const SizedBox(height: 16),

                    // Class
                    const Text('Class',
                        style: TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: List.generate(5, (i) {
                        final grade = i + 8;
                        final selected = classGrade == grade;
                        return ChoiceChip(
                          label: Text('$grade'),
                          selected: selected,
                          onSelected: (_) {
                            setDialogState(() {
                              classGrade = grade;
                              if (grade < 11) stream = null;
                            });
                          },
                        );
                      }),
                    ),
                    const SizedBox(height: 16),

                    // Stream (for 11-12)
                    if (needsStream) ...[
                      const Text('Stream',
                          style: TextStyle(
                              fontWeight: FontWeight.w600, fontSize: 13)),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<String>(
                        initialValue: stream ?? 'science',
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                        items: ['science', 'commerce', 'arts']
                            .map((s) => DropdownMenuItem(
                                value: s,
                                child:
                                    Text(s[0].toUpperCase() + s.substring(1))))
                            .toList(),
                        onChanged: (v) {
                          if (v != null) setDialogState(() => stream = v);
                        },
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx, false),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, true),
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result == true && mounted) {
      try {
        await auth.updateProfile(
          curriculum: curriculum,
          classGrade: classGrade,
          stream: classGrade >= 11 ? (stream ?? 'science') : null,
        );
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Class updated successfully!')),
          );
          _loadStats(); // reload stats for new class
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final themeService = context.watch<ThemeService>();
    final locService = context.watch<LocalizationService>();
    final theme = Theme.of(context);
    final user = auth.user!;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Avatar + name ──
          Center(
            child: Column(
              children: [
                CircleAvatar(
                  radius: 48,
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Text(
                    user.name.isNotEmpty ? user.name[0].toUpperCase() : '?',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(user.name,
                    style: theme.textTheme.headlineSmall
                        ?.copyWith(fontWeight: FontWeight.bold)),
                Text(user.email,
                    style: theme.textTheme.bodyMedium
                        ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Academic info (editable class) ──
          const _SectionHeader(title: 'Academic Info'),
          Card(
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Column(
              children: [
                _InfoTile(
                  icon: Icons.school_rounded,
                  label: 'Curriculum',
                  value: user.curriculum ?? 'Not set',
                ),
                const Divider(height: 1, indent: 56),
                ListTile(
                  leading: const Icon(Icons.class_rounded),
                  title: const Text('Class'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        user.classGrade?.toString() ?? 'Not set',
                        style: const TextStyle(fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: Icon(Icons.edit_rounded,
                            size: 20, color: theme.colorScheme.primary),
                        tooltip: 'Change class',
                        onPressed: _showEditClassDialog,
                      ),
                    ],
                  ),
                ),
                if (user.stream != null) ...[
                  const Divider(height: 1, indent: 56),
                  _InfoTile(
                    icon: Icons.alt_route_rounded,
                    label: 'Stream',
                    value: user.stream!,
                  ),
                ],
                const Divider(height: 1, indent: 56),
                _InfoTile(
                  icon: Icons.language_rounded,
                  label: 'Language',
                  value: AppConstants
                          .supportedLanguages[user.languagePreference] ??
                      user.languagePreference,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Subject Skills & Time ──
          const _SectionHeader(title: 'Subject Skills & Time'),
          if (_loadingStats)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_stats.isEmpty)
            Card(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              child: const Padding(
                padding: EdgeInsets.all(24),
                child: Center(
                  child: Text(
                    'No study data yet.\nStart learning to see your progress here!',
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            )
          else
            ..._stats.map((stat) => _buildStatCard(stat, theme)),
          const SizedBox(height: 20),

          // ── Preferences ──
          const _SectionHeader(title: 'Preferences'),
          Card(
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Column(
              children: [
                // Dark mode toggle
                SwitchListTile(
                  secondary: Icon(
                    themeService.isDark
                        ? Icons.dark_mode_rounded
                        : Icons.light_mode_rounded,
                  ),
                  title: const Text('Dark Mode'),
                  value: themeService.isDark,
                  onChanged: (_) => themeService.toggle(),
                ),
                const Divider(height: 1, indent: 56),
                // Language
                ListTile(
                  leading: const Icon(Icons.translate_rounded),
                  title: const Text('Language'),
                  trailing: DropdownButton<String>(
                    value: locService.languageCode,
                    underline: const SizedBox.shrink(),
                    items: AppConstants.supportedLanguages.entries
                        .map((e) => DropdownMenuItem(
                              value: e.key,
                              child: Text(e.value),
                            ))
                        .toList(),
                    onChanged: (code) {
                      if (code != null) {
                        locService.setLanguage(code);
                        // Also update backend so AI content uses this language
                        auth.updateProfile(languagePreference: code);
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── About ──
          const _SectionHeader(title: 'About'),
          Card(
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: const Column(
              children: [
                _InfoTile(
                  icon: Icons.info_outline_rounded,
                  label: 'Version',
                  value: '1.0.0',
                ),
                Divider(height: 1, indent: 56),
                _InfoTile(
                  icon: Icons.favorite_rounded,
                  label: 'Built for',
                  value: 'Rural India',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Logout ──
          FilledButton.tonal(
            onPressed: () async {
              await auth.logout();
              if (context.mounted) {
                Navigator.of(context).popUntil((route) => route.isFirst);
              }
            },
            style: FilledButton.styleFrom(
              backgroundColor: theme.colorScheme.errorContainer,
              foregroundColor: theme.colorScheme.onErrorContainer,
              minimumSize: const Size.fromHeight(48),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('Logout', style: TextStyle(fontSize: 16)),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildStatCard(Map<String, dynamic> stat, ThemeData theme) {
    final name = stat['subject_name'] as String? ?? 'Unknown';
    final avgScore = stat['avg_quiz_score'] as num?;
    final totalFc = stat['total_flashcards_reviewed'] as int? ?? 0;
    final totalTime = stat['total_time_spent_seconds'] as int? ?? 0;
    final completed = stat['chapters_completed'] as int? ?? 0;
    final total = stat['total_chapters'] as int? ?? 0;

    // Skill level based on quiz score
    String skillLabel;
    Color skillColor;
    if (avgScore == null) {
      skillLabel = 'Not started';
      skillColor = Colors.grey;
    } else if (avgScore >= 80) {
      skillLabel = 'Advanced';
      skillColor = Colors.green;
    } else if (avgScore >= 50) {
      skillLabel = 'Intermediate';
      skillColor = Colors.orange;
    } else {
      skillLabel = 'Beginner';
      skillColor = Colors.red;
    }

    final progress = total > 0 ? completed / total : 0.0;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Subject name + skill badge
            Row(
              children: [
                Expanded(
                  child: Text(name,
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: skillColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(skillLabel,
                      style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: skillColor)),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 6,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
                color: skillColor,
              ),
            ),
            const SizedBox(height: 6),
            Text('$completed / $total chapters completed',
                style: TextStyle(
                    fontSize: 12, color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 10),
            // Stats row
            Row(
              children: [
                _miniStat(Icons.timer_outlined, _formatTime(totalTime), 'Time',
                    theme),
                const SizedBox(width: 16),
                _miniStat(
                    Icons.quiz_outlined,
                    avgScore != null ? '${avgScore.toStringAsFixed(0)}%' : '—',
                    'Quiz Score',
                    theme),
                const SizedBox(width: 16),
                _miniStat(
                    Icons.style_outlined, '$totalFc', 'Cards Reviewed', theme),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _miniStat(IconData icon, String value, String label, ThemeData theme) {
    return Expanded(
      child: Row(
        children: [
          Icon(icon, size: 16, color: theme.colorScheme.primary),
          const SizedBox(width: 4),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value,
                    style: const TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w600)),
                Text(label,
                    style: TextStyle(
                        fontSize: 10,
                        color: theme.colorScheme.onSurfaceVariant),
                    overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(title,
          style: Theme.of(context)
              .textTheme
              .titleSmall
              ?.copyWith(fontWeight: FontWeight.bold)),
    );
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _InfoTile(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label),
      trailing:
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
    );
  }
}
