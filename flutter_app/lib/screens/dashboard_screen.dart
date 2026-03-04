import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/services/auth_service.dart';
import 'package:smart_shiksha/services/theme_service.dart';
import 'package:smart_shiksha/screens/lessons_browser_screen.dart';
import 'package:smart_shiksha/screens/quiz_screen.dart';
import 'package:smart_shiksha/screens/revision_screen.dart';
import 'package:smart_shiksha/screens/ai_tutor_screen.dart';
import 'package:smart_shiksha/screens/exam_prep_screen.dart';
import 'package:smart_shiksha/screens/profile_screen.dart';

/// Main dashboard with 6 navigation cards.
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final themeService = context.watch<ThemeService>();
    final user = auth.user!;
    final theme = Theme.of(context);

    final cards = <_DashCard>[
      _DashCard(
        title: 'Lessons',
        subtitle: 'Browse your syllabus',
        icon: Icons.menu_book_rounded,
        gradient: const [Color(0xFF1565C0), Color(0xFF42A5F5)],
        onTap: () => Navigator.push(context,
            MaterialPageRoute(builder: (_) => const LessonsBrowserScreen())),
      ),
      _DashCard(
        title: 'Quizzes',
        subtitle: 'Test your knowledge',
        icon: Icons.quiz_rounded,
        gradient: const [Color(0xFF2E7D32), Color(0xFF66BB6A)],
        onTap: () => Navigator.push(
            context, MaterialPageRoute(builder: (_) => const QuizScreen())),
      ),
      _DashCard(
        title: 'Revision',
        subtitle: 'Review saved lessons',
        icon: Icons.replay_rounded,
        gradient: const [Color(0xFFE65100), Color(0xFFFF9800)],
        onTap: () => Navigator.push(
            context, MaterialPageRoute(builder: (_) => const RevisionScreen())),
      ),
      _DashCard(
        title: 'AI Tutor',
        subtitle: 'Ask anything',
        icon: Icons.smart_toy_rounded,
        gradient: const [Color(0xFF6A1B9A), Color(0xFFAB47BC)],
        onTap: () => Navigator.push(
            context, MaterialPageRoute(builder: (_) => const AiTutorScreen())),
      ),
      _DashCard(
        title: 'Exam Prep',
        subtitle: (user.classGrade ?? 10) <= 9
            ? 'Final exam practice'
            : (user.classGrade == 10)
                ? 'Board exam practice'
                : 'JEE / NEET practice',
        icon: Icons.emoji_events_rounded,
        gradient: const [Color(0xFFC62828), Color(0xFFEF5350)],
        onTap: () => Navigator.push(
            context, MaterialPageRoute(builder: (_) => const ExamPrepScreen())),
      ),
      _DashCard(
        title: 'Profile',
        subtitle: 'Settings & progress',
        icon: Icons.person_rounded,
        gradient: const [Color(0xFF37474F), Color(0xFF78909C)],
        onTap: () => Navigator.push(
            context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Shiksha'),
        actions: [
          IconButton(
            icon:
                Icon(themeService.isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: () => themeService.toggle(),
            tooltip: 'Toggle theme',
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Greeting
              Text(
                'Hello, ${user.name}! 👋',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${user.curriculum ?? ""} • Class ${user.classGrade ?? ""}${user.stream != null ? " • ${user.stream}" : ""}',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 24),

              // Grid of cards
              Expanded(
                child: GridView.builder(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 16,
                    crossAxisSpacing: 16,
                    childAspectRatio: 1.1,
                  ),
                  itemCount: cards.length,
                  itemBuilder: (context, index) {
                    final card = cards[index];
                    return _buildCard(context, card);
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCard(BuildContext context, _DashCard card) {
    return InkWell(
      onTap: card.onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: card.gradient,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: card.gradient[0].withValues(alpha: 0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(card.icon, size: 40, color: Colors.white),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  card.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  card.subtitle,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.85),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DashCard {
  final String title;
  final String subtitle;
  final IconData icon;
  final List<Color> gradient;
  final VoidCallback onTap;

  const _DashCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.gradient,
    required this.onTap,
  });
}
