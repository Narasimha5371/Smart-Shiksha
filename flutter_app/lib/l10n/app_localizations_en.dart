// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Smart Shiksha';

  @override
  String get tagline => 'AI-powered learning for every student';

  @override
  String get selectLanguage => 'Language';

  @override
  String get askHeading => 'Ask a Question';

  @override
  String get questionPlaceholder => 'Type your question here…';

  @override
  String get askButton => 'Get Lesson';

  @override
  String get loading => 'Generating your lesson…';

  @override
  String get lessonHeading => 'Your Lesson';

  @override
  String get saveLesson => 'Save Lesson';

  @override
  String get lessonSaved => 'Saved!';

  @override
  String get sourcesHeading => 'Sources';

  @override
  String get savedHeading => 'Saved Lessons';

  @override
  String get noSavedLessons =>
      'No saved lessons yet. Ask a question to get started!';

  @override
  String get footerText => 'Education for All';

  @override
  String get settings => 'Settings';

  @override
  String get errorGeneric => 'Something went wrong. Please try again.';
}
