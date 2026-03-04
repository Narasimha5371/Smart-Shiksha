/// Data model for a user.
class AppUser {
  final String id;
  final String name;
  final String email;
  final String? profilePictureUrl;
  final String languagePreference;
  final String? curriculum;
  final int? classGrade;
  final String? stream;
  final bool onboardingComplete;
  final DateTime? createdAt;

  const AppUser({
    required this.id,
    required this.name,
    required this.email,
    this.profilePictureUrl,
    this.languagePreference = 'en',
    this.curriculum,
    this.classGrade,
    this.stream,
    this.onboardingComplete = false,
    this.createdAt,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      profilePictureUrl: json['profile_picture_url'] as String?,
      languagePreference: json['language_preference'] as String? ?? 'en',
      curriculum: json['curriculum'] as String?,
      classGrade: json['class_grade'] as int?,
      stream: json['stream'] as String?,
      onboardingComplete: json['onboarding_complete'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }
}
