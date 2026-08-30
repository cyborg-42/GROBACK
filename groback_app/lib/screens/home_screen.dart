import 'package:flutter/material.dart';
import 'package:groback_app/services/api_service.dart';
import 'package:groback_app/models/grocery_item.dart';
import 'package:groback_app/models/scan_log.dart';
import 'package:groback_app/models/depletion_metric.dart';
import '../widgets/weight_card.dart';
import '../widgets/detection_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late Future<List<GroceryItem>> _inventoryFuture;
  late Future<List<ScanLog>> _scansFuture;
  late Future<List<DepletionMetric>> _depletionFuture;
  late Future<Map<String, dynamic>> _summaryFuture;

  @override
  void initState() {
    super.initState();
    _refreshData();
  }

  void _refreshData() {
    setState(() {
      _inventoryFuture = ApiService.getInventory();
      _scansFuture = ApiService.getRecentScans();
      _depletionFuture = ApiService.getDepletionMetrics();
      _summaryFuture = ApiService.getInventorySummary();
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refreshData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Greeting
            Text(
              'Hello, GroBack User!',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Your smart shelf is ready for scanning.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),

            // Quick AI Scan Banner Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  // Navigate to scan screen
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const ScanScreen()),
                  );
                },
                icon: const Icon(Icons.center_focus_strong),
                label: const Text('Quick AI Scan'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Summary Cards
            Row(
              children: [
                Expanded(
                  child: _buildSummaryCard(
                    'Total Items',
                    '4',
                    Icons.inventory,
                    AppTheme.forestEmerald,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildSummaryCard(
                    'Total Weight',
                    '1.33 kg', // This would be calculated from inventory
                    Icons.monitor_weight,
                    AppTheme.mintLeaf,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Low Stock Depletion Alerts Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Depletion Alerts',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    FutureBuilder<List<DepletionMetric>>(
                      future: _depletionFuture,
                      builder: (context, snapshot) {
                        if (snapshot.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        if (snapshot.hasError) {
                          return Text('Error: ${snapshot.error}');
                        }
                        final metrics = snapshot.data ?? [];
                        final lowStock = metrics.where((m) =>
                            m.stockStatus == 'Low Stock' || m.stockStatus == 'Critical').toList();
                        if (lowStock.isEmpty) {
                          return const Text('All items are sufficiently stocked.');
                        }
                        return Column(
                          children: lowStock.map((metric) => ListTile(
                            leading: Icon(
                              metric.stockStatus == 'Critical'
                                  ? Icons.error
                                  : Icons.warning,
                              color: metric.stockStatus == 'Critical'
                                  ? AppTheme.criticalAlert
                                  : AppTheme.lowStockAlert,
                            ),
                            title: Text('${metric.itemName} (Q${metric.quadrant})'),
                            subtitle: Text(
                              '${metric.estimatedDaysRemaining.toStringAsFixed(1)} days left',
                              style: TextStyle(
                                color: metric.stockStatus == 'Critical'
                                    ? AppTheme.criticalAlert
                                    : AppTheme.lowStockAlert,
                              ),
                            ),
                          )).toList(),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Recent AI Scan History Feed
            Text(
              'Recent Scans',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            FutureBuilder<List<ScanLog>>(
              future: _scansFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Text('Error: ${snapshot.error}');
                }
                final scans = snapshot.data ?? [];
                if (scans.isEmpty) {
                  return const Text('No scans yet.');
                }
                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: scans.length,
                  itemBuilder: (context, index) {
                    final scan = scans[index];
                    return DetectionCard(
                      label: scan.label,
                      confidence: scan.confidence,
                      timestamp: scan.timestamp,
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(String title, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}