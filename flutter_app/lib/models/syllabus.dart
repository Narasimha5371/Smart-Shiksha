/// Data model for a subject from the syllabus.
class Subject {
  final String id;
  final String name;
  final String curriculum;
  final int classGrade;
  final String? stream;
  final String? iconName;

  const Subject({
    required this.id,
    required this.name,
    required this.curriculum,
    required this.classGrade,
    this.stream,
    this.iconName,
  });

  factory Subject.fromJson(Map<String, dynamic> json) {
    return Subject(
      id: json['id'] as String,
      name: json['name'] as String,
      curriculum: json['curriculum'] as String,
      classGrade: json['class_grade'] as int,
      stream: json['stream'] as String?,
      iconName: json['icon_name'] as String?,
    );
  }
}

/// Data model for a chapter.
class Chapter {
  final String id;
  final String subjectId;
  final String title;
  final int order;
  final String? description;

  const Chapter({
    required this.id,
    required this.subjectId,
    required this.title,
    required this.order,
    this.description,
  });

  factory Chapter.fromJson(Map<String, dynamic> json) {
    return Chapter(
      id: json['id'] as String,
      subjectId: json['subject_id'] as String,
      title: json['title'] as String,
      order: json['order'] as int,
      description: json['description'] as String?,
    );
  }
}

/// Data model for a generated lesson.
class GeneratedLesson {
  final String id;
  final String chapterId;
  final String title;
  final String contentMarkdown;
  final String? imageUrl;
  final String languageCode;
  final int order;
  final DateTime? createdAt;

  const GeneratedLesson({
    required this.id,
    required this.chapterId,
    required this.title,
    required this.contentMarkdown,
    this.imageUrl,
    this.languageCode = 'en',
    this.order = 0,
    this.createdAt,
  });

  factory GeneratedLesson.fromJson(Map<String, dynamic> json) {
    return GeneratedLesson(
      id: json['id'] as String,
      chapterId: json['chapter_id'] as String,
      title: json['title'] as String,
      contentMarkdown: json['content_markdown'] as String,
      imageUrl: json['image_url'] as String?,
      languageCode: json['language_code'] as String? ?? 'en',
      order: json['order'] as int? ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }
}

/// Quiz question — supports MCQ, MSQ, and Numerical types.
class FlashCard {
  final String id;
  final String chapterId;
  final String question;
  final String answer;           // "B" for MCQ, "A,C" for MSQ, "42" for numerical
  final String questionType;     // "mcq" | "msq" | "numerical"
  final List<String>? options;   // ["A. …", "B. …", …]  — null for numerical
  final String? explanation;
  final int order;

  const FlashCard({
    required this.id,
    required this.chapterId,
    required this.question,
    required this.answer,
    this.questionType = 'mcq',
    this.options,
    this.explanation,
    this.order = 0,
  });

  factory FlashCard.fromJson(Map<String, dynamic> json) {
    return FlashCard(
      id: json['id'] as String,
      chapterId: json['chapter_id'] as String,
      question: json['question'] as String,
      answer: json['answer'] as String? ?? '',
      questionType: json['question_type'] as String? ?? 'mcq',
      options: (json['options_json'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      explanation: json['explanation'] as String?,
      order: json['order'] as int? ?? 0,
    );
  }

  /// Extract just the letter key from an option string like "A. Newton's law" → "A"
  static String optionKey(String option) {
    if (option.length >= 2 && option[1] == '.') return option[0];
    return option;
  }

  /// Correct answer keys as a set: {"B"} for MCQ, {"A","C"} for MSQ
  Set<String> get correctKeys =>
      answer.split(',').map((s) => s.trim().toUpperCase()).toSet();
}

/// Competitive exam metadata.
class CompetitiveExam {
  final String id;
  final String name;
  final String? description;
  final List<String> subjects;

  const CompetitiveExam({
    required this.id,
    required this.name,
    this.description,
    this.subjects = const [],
  });

  factory CompetitiveExam.fromJson(Map<String, dynamic> json) {
    return CompetitiveExam(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      subjects: (json['subjects_json'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }
}

/// Mock test.
class MockTest {
  final String id;
  final String examId;
  final String title;
  final List<dynamic>? questionsJson;
  final int durationMinutes;
  final int totalMarks;
  final DateTime? createdAt;

  const MockTest({
    required this.id,
    required this.examId,
    required this.title,
    this.questionsJson,
    this.durationMinutes = 180,
    this.totalMarks = 360,
    this.createdAt,
  });

  factory MockTest.fromJson(Map<String, dynamic> json) {
    return MockTest(
      id: json['id'] as String,
      examId: json['exam_id'] as String,
      title: json['title'] as String,
      questionsJson: json['questions_json'] as List<dynamic>?,
      durationMinutes: json['duration_minutes'] as int? ?? 180,
      totalMarks: json['total_marks'] as int? ?? 360,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }
}
