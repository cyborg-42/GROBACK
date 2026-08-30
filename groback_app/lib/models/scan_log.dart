class ScanLog {
  final int id;
  final String label;
  final double confidence;
  final String timestamp;

  ScanLog({
    required this.id,
    required this.label,
    required this.confidence,
    required this.timestamp,
  });

  factory ScanLog.fromJson(Map<String, dynamic> json) {
    return ScanLog(
      id: json['id'] as int,
      label: json['label'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      timestamp: json['timestamp'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'label': label,
      'confidence': confidence,
      'timestamp': timestamp,
    };
  }
}