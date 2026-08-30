class DepletionMetric {
  final String itemName;
  final int quadrant;
  final double currentWeightG;
  final double dailyRateG;
  final double estimatedDaysRemaining;
  final String stockStatus;

  DepletionMetric({
    required this.itemName,
    required this.quadrant,
    required this.currentWeightG,
    required this.dailyRateG,
    required this.estimatedDaysRemaining,
    required this.stockStatus,
  });

  factory DepletionMetric.fromJson(Map<String, dynamic> json) {
    return DepletionMetric(
      itemName: json['item_name'] as String,
      quadrant: json['quadrant'] as int,
      currentWeightG: (json['current_weight_g'] as num).toDouble(),
      dailyRateG: (json['daily_rate_g'] as num).toDouble(),
      estimatedDaysRemaining: (json['estimated_days_remaining'] as num).toDouble(),
      stockStatus: json['stock_status'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'item_name': itemName,
      'quadrant': quadrant,
      'current_weight_g': currentWeightG,
      'daily_rate_g': dailyRateG,
      'estimated_days_remaining': estimatedDaysRemaining,
      'stock_status': stockStatus,
    };
  }
}