import 'package:flutter/material.dart';
import 'package:groback_app/theme/app_theme.dart';

class DetectionCard extends StatelessWidget {
  final String label;
  final double confidence;
  final String timestamp;

  const DetectionCard({
    Key? key,
    required this.label,
    required this.confidence,
    required this.timestamp,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            // Icon representing the item (placeholder)
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: AppTheme.mintLeaf.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                _getIconForLabel(label),
                color: AppTheme.forestEmerald,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Confidence: ${confidence.toStringAsFixed(1)}%',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            Text(
              timestamp,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  IconData _getIconForLabel(String label) {
    switch (label.toLowerCase()) {
      case 'apple':
        return Icons.apple;
      case 'banana':
        return Icons.straighten; // There's no banana icon, using a placeholder
      case 'orange':
        return Icons.brightness_5; // Placeholder for orange
      case 'carrot':
        return Icons.zoom_in; // Placeholder for carrot
      default:
        return Icons.fastfood; // Generic food icon
    }
  }
}