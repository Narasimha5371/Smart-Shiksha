/// Data model for a lesson returned by or saved to the API.
class Lesson {
  final String? id;
  final String topic;
  final String content;
  final String languageCode;
  final List<String> sources;
  final DateTime? createdAt;

  const Lesson({
    this.id,
    required this.topic,
    required this.content,
    required this.languageCode,
    this.sources = const [],
    this.createdAt,
  });

  factory Lesson.fromAskJson(Map<String, dynamic> json) {
    return Lesson(
      topic: json['topic'] as String? ?? '',
      content: json['content'] as String? ?? '',
      languageCode: json['language'] as String? ?? 'en',
      sources:
          (json['sources'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  factory Lesson.fromSavedJson(Map<String, dynamic> json) {
    return Lesson(
      id: json['id'] as String?,
      topic: json['topic'] as String? ?? '',
      content: json['content'] as String? ?? '',
      languageCode: json['language_code'] as String? ?? 'en',
      sources:
          (json['source_urls'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toDbMap() => {
    'id': id,
    'topic': topic,
    'content': content,
    'language_code': languageCode,
    'sources': sources.join('|||'),
    'created_at': (createdAt ?? DateTime.now()).toIso8601String(),
  };

  factory Lesson.fromDbMap(Map<String, dynamic> map) {
    return Lesson(
      id: map['id'] as String?,
      topic: map['topic'] as String? ?? '',
      content: map['content'] as String? ?? '',
      languageCode: map['language_code'] as String? ?? 'en',
      sources: (map['sources'] as String?)?.split('|||') ?? [],
      createdAt: map['created_at'] != null
          ? DateTime.tryParse(map['created_at'] as String)
          : null,
    );
  }
}
