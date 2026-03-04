// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Tamil (`ta`).
class AppLocalizationsTa extends AppLocalizations {
  AppLocalizationsTa([String locale = 'ta']) : super(locale);

  @override
  String get appTitle => 'ஸ்மார்ட் சிக்ஷா';

  @override
  String get tagline => 'ஒவ்வொரு மாணவருக்கும் AI-இயக்கும் கல்வி';

  @override
  String get selectLanguage => 'மொழி';

  @override
  String get askHeading => 'கேள்வி கேளுங்கள்';

  @override
  String get questionPlaceholder => 'உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யவும்…';

  @override
  String get askButton => 'பாடம் பெறுங்கள்';

  @override
  String get loading => 'உங்கள் பாடம் உருவாக்கப்படுகிறது…';

  @override
  String get lessonHeading => 'உங்கள் பாடம்';

  @override
  String get saveLesson => 'பாடத்தைச் சேமிக்கவும்';

  @override
  String get lessonSaved => 'சேமிக்கப்பட்டது!';

  @override
  String get sourcesHeading => 'ஆதாரங்கள்';

  @override
  String get savedHeading => 'சேமித்த பாடங்கள்';

  @override
  String get noSavedLessons =>
      'இன்னும் சேமித்த பாடங்கள் இல்லை. தொடங்க ஒரு கேள்வி கேளுங்கள்!';

  @override
  String get footerText => 'அனைவருக்கும் கல்வி';

  @override
  String get settings => 'அமைப்புகள்';

  @override
  String get errorGeneric => 'ஏதோ தவறு நடந்தது. மீண்டும் முயற்சிக்கவும்.';
}
