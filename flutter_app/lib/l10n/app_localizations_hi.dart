// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'स्मार्ट शिक्षा';

  @override
  String get tagline => 'हर छात्र के लिए AI-संचालित शिक्षा';

  @override
  String get selectLanguage => 'भाषा';

  @override
  String get askHeading => 'सवाल पूछें';

  @override
  String get questionPlaceholder => 'अपना सवाल यहाँ लिखें…';

  @override
  String get askButton => 'पाठ प्राप्त करें';

  @override
  String get loading => 'आपका पाठ तैयार हो रहा है…';

  @override
  String get lessonHeading => 'आपका पाठ';

  @override
  String get saveLesson => 'पाठ सहेजें';

  @override
  String get lessonSaved => 'सहेजा गया!';

  @override
  String get sourcesHeading => 'स्रोत';

  @override
  String get savedHeading => 'सहेजे गए पाठ';

  @override
  String get noSavedLessons =>
      'अभी कोई सहेजा गया पाठ नहीं है। शुरू करने के लिए एक सवाल पूछें!';

  @override
  String get footerText => 'सबके लिए शिक्षा';

  @override
  String get settings => 'सेटिंग्स';

  @override
  String get errorGeneric => 'कुछ गलत हो गया। कृपया पुनः प्रयास करें।';
}
