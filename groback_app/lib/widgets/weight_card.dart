import 'package:flutter/material.dart';
import 'package:groback_app/theme/app_theme.dart';

class WeightCard extends StatelessWidget {
  final String label;
  final double weight;
  final double maxCapacity;
  final String status;
  final int quadrant;

  const WeightCard({
    Key? key,
    required this.label,
    required this.weight,
    required this.maxCapacity,
    required this.status,
    required this.quadrant,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Quadrant $quadrant',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getStatusColor(status).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    status,
                    style: TextStyle(
                      color: _getStatusColor(status),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(height: 1),
            const SizedBox(height: 8),
            Text(
              label,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 4),
            Text(
              'Weight: ${weight.toStringAsFixed(1)} g / ${maxCapacity.toStringAsFixed(0)} g',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 8,
              child: LinearProgressIndicator(
                value: weight / maxCapacity,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(_getStatusColor(status)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Critical':
        return AppTheme.criticalAlert;
      case 'Low Stock':
        return AppTheme.lowStockAlert;
      default:
        return AppTheme.mintLeaf;
    }
  }
}