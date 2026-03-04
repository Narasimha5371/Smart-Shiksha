import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/services/auth_service.dart';
import 'package:smart_shiksha/services/api_service.dart';

/// Onboarding wizard: Curriculum → Class → Stream → Language.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _api = ApiService();
  int _step = 0; // 0=curriculum, 1=class, 2=stream (if 11-12), 3=language
  List<String> _curricula = [];
  bool _loading = true;

  String? _selectedCurriculum;
  int? _selectedClass;
  String? _selectedStream;
  String _selectedLanguage = 'en';

  final _languages = {
    'en': 'English',
    'hi': 'हिन्दी (Hindi)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'te': 'తెలుగు (Telugu)',
    'ta': 'தமிழ் (Tamil)',
  };

  @override
  void initState() {
    super.initState();
    _loadCurricula();
  }

  Future<void> _loadCurricula() async {
    final curricula = await _api.getCurricula();
    setState(() {
      _curricula = curricula;
      _loading = false;
    });
  }

  bool get _needsStream => _selectedClass != null && _selectedClass! >= 11;

  void _next() {
    if (_step == 0 && _selectedCurriculum != null) {
      setState(() => _step = 1);
    } else if (_step == 1 && _selectedClass != null) {
      if (_needsStream) {
        setState(() => _step = 2);
      } else {
        setState(() => _step = 3);
      }
    } else if (_step == 2 && _selectedStream != null) {
      setState(() => _step = 3);
    }
  }

  void _back() {
    if (_step == 3 && _needsStream) {
      setState(() => _step = 2);
    } else if (_step == 3) {
      setState(() => _step = 1);
    } else if (_step > 0) {
      setState(() => _step -= 1);
    }
  }

  Future<void> _complete() async {
    final auth = context.read<AuthService>();
    await auth.completeOnboarding(
      curriculum: _selectedCurriculum!,
      classGrade: _selectedClass!,
      stream: _needsStream ? _selectedStream : null,
      languagePreference: _selectedLanguage,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final auth = context.watch<AuthService>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Setup Your Profile'),
        leading: _step > 0
            ? IconButton(icon: const Icon(Icons.arrow_back), onPressed: _back)
            : null,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Progress indicator
                  LinearProgressIndicator(
                    value: (_step + 1) / (_needsStream ? 4 : 3),
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                  const SizedBox(height: 24),

                  // Step content
                  Expanded(child: _buildStep(theme)),

                  // Action buttons
                  if (_step < 3)
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _canProceed() ? _next : null,
                        child: const Text('Continue'),
                      ),
                    ),
                  if (_step == 3)
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: auth.isLoading ? null : _complete,
                        child: auth.isLoading
                            ? const CircularProgressIndicator()
                            : const Text('Start Learning!'),
                      ),
                    ),
                ],
              ),
            ),
    );
  }

  bool _canProceed() {
    switch (_step) {
      case 0:
        return _selectedCurriculum != null;
      case 1:
        return _selectedClass != null;
      case 2:
        return _selectedStream != null;
      default:
        return true;
    }
  }

  Widget _buildStep(ThemeData theme) {
    switch (_step) {
      case 0:
        return _buildCurriculumStep(theme);
      case 1:
        return _buildClassStep(theme);
      case 2:
        return _buildStreamStep(theme);
      case 3:
        return _buildLanguageStep(theme);
      default:
        return const SizedBox();
    }
  }

  Widget _buildCurriculumStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Select Your Board / Curriculum',
            style: theme.textTheme.titleLarge),
        const SizedBox(height: 8),
        Text('Choose the board your school follows',
            style: theme.textTheme.bodyMedium),
        const SizedBox(height: 16),
        Expanded(
          child: ListView.builder(
            itemCount: _curricula.length,
            itemBuilder: (ctx, i) {
              final c = _curricula[i];
              return RadioListTile<String>(
                title: Text(c),
                value: c,
                groupValue: _selectedCurriculum,
                onChanged: (v) => setState(() => _selectedCurriculum = v),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildClassStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Select Your Class', style: theme.textTheme.titleLarge),
        const SizedBox(height: 16),
        Expanded(
          child: GridView.builder(
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.2,
            ),
            itemCount: 5, // classes 8-12
            itemBuilder: (ctx, i) {
              final grade = i + 8;
              final selected = _selectedClass == grade;
              return InkWell(
                onTap: () => setState(() => _selectedClass = grade),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  decoration: BoxDecoration(
                    color: selected
                        ? theme.colorScheme.primary
                        : theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(12),
                    border: selected
                        ? Border.all(color: theme.colorScheme.primary, width: 2)
                        : null,
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    'Class\n$grade',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: selected
                          ? theme.colorScheme.onPrimary
                          : theme.colorScheme.onSurface,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildStreamStep(ThemeData theme) {
    final streams = ['science', 'commerce', 'arts'];
    final streamLabels = {
      'science': 'Science',
      'commerce': 'Commerce',
      'arts': 'Arts'
    };
    final streamIcons = {
      'science': Icons.science,
      'commerce': Icons.business,
      'arts': Icons.palette,
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Select Your Stream', style: theme.textTheme.titleLarge),
        const SizedBox(height: 8),
        Text('Choose your course stream for Class $_selectedClass',
            style: theme.textTheme.bodyMedium),
        const SizedBox(height: 24),
        ...streams.map((s) => Card(
              child: ListTile(
                leading: Icon(streamIcons[s], size: 32),
                title: Text(streamLabels[s]!,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                selected: _selectedStream == s,
                selectedColor: theme.colorScheme.primary,
                selectedTileColor: theme.colorScheme.primaryContainer,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
                onTap: () => setState(() => _selectedStream = s),
              ),
            )),
      ],
    );
  }

  Widget _buildLanguageStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Preferred Language', style: theme.textTheme.titleLarge),
        const SizedBox(height: 8),
        Text('Lessons will be generated in this language',
            style: theme.textTheme.bodyMedium),
        const SizedBox(height: 16),
        ..._languages.entries.map((e) => RadioListTile<String>(
              title: Text(e.value),
              value: e.key,
              groupValue: _selectedLanguage,
              onChanged: (v) => setState(() => _selectedLanguage = v ?? 'en'),
            )),
        const Spacer(),
        // Summary
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Your Selection', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                Text('Board: $_selectedCurriculum'),
                Text('Class: $_selectedClass'),
                if (_selectedStream != null) Text('Stream: $_selectedStream'),
                Text('Language: ${_languages[_selectedLanguage]}'),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
