import 'package:flutter/material.dart';
import 'package:groback_app/services/api_service.dart';
import 'package:groback_app/services/ws_service.dart';
import 'package:groback_app/models/grocery_item.dart';
import 'package:groback_app/models/scan_log.dart';
import 'package:groback_app/models/depletion_metric.dart';
import 'package:groback_app/theme/app_theme.dart';
import 'scan_screen.dart';
import '../widgets/detection_card.dart';
import '../widgets/offline_banner.dart';
import 'dart:async';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<GroceryItem> _inventory = [];
  List<ScanLog> _scans = [];
  List<DepletionMetric> _depletion = [];
  bool _isLoading = true;
  bool _isOnline = true;
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  void initState() {
    super.initState();
    WsService.instance.connect();
    _wsSub = WsService.instance.stream.listen(_onWsMessage);
    _refreshData();
  }

  void _onWsMessage(Map<String, dynamic> msg) {
    final type = msg['type'] as String?;
    if (type == 'SCAN_UPDATE') {
      // Prepend the new scan to the list without a full reload
      final newScan = ScanLog(
        id: 0,
        label: msg['label'] as String,
        confidence: (msg['confidence'] as num).toDouble(),
        timestamp: 'Just now',
      );
      if (mounted) setState(() => _scans = [newScan, ..._scans]);
    } else if (type == 'WEIGHT_UPDATE') {
      // Refresh inventory to reflect the new weight
      _refreshData();
    }
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    super.dispose();
  }

  Future<void> _refreshData() async {
    setState(() => _isLoading = true);

    final inventoryResult = await ApiService.getInventory();
    final scansResult = await ApiService.getRecentScans();
    final depletionResult = await ApiService.getDepletionMetrics();

    if (!mounted) return;

    // If any call reached the backend, consider ourselves online.
    final online =
        inventoryResult.isOnline || scansResult.isOnline || depletionResult.isOnline;

    setState(() {
      _inventory = inventoryResult.data;
      _scans = scansResult.data;
      _depletion = depletionResult.data;
      _isOnline = online;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final totalWeightKg =
        _inventory.fold<double>(0, (sum, i) => sum + i.weightG) / 1000.0;
    final itemCount = _inventory.length;
    final lowStockItems = _depletion
        .where((m) => m.stockStatus == 'Low Stock' || m.stockStatus == 'Critical')
        .toList();

    return RefreshIndicator(
      onRefresh: _refreshData,
      child: Column(
        children: [
          OfflineBanner(visible: !_isOnline),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : SingleChildScrollView(
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

                        // Quick AI Scan Button
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                    builder: (_) => const ScanScreen()),
                              );
                            },
                            icon: const Icon(Icons.center_focus_strong),
                            label: const Text('Quick AI Scan'),
                            style: ElevatedButton.styleFrom(
                              padding:
                                  const EdgeInsets.symmetric(vertical: 16),
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
                                _isOnline ? '$itemCount' : '—',
                                Icons.inventory,
                                AppTheme.forestEmerald,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: _buildSummaryCard(
                                'Total Weight',
                                _isOnline
                                    ? '${totalWeightKg.toStringAsFixed(2)} kg'
                                    : '—',
                                Icons.monitor_weight,
                                AppTheme.mintLeaf,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),

                        // Depletion Alerts
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
                                if (!_isOnline)
                                  const Text(
                                    'No data — backend is offline.',
                                    style: TextStyle(
                                        color: AppTheme.textSecondary),
                                  )
                                else if (lowStockItems.isEmpty)
                                  const Text(
                                      'All items are sufficiently stocked.')
                                else
                                  ...lowStockItems.map((metric) => ListTile(
                                        leading: Icon(
                                          metric.stockStatus == 'Critical'
                                              ? Icons.error
                                              : Icons.warning,
                                          color: metric.stockStatus == 'Critical'
                                              ? AppTheme.criticalAlert
                                              : AppTheme.lowStockAlert,
                                        ),
                                        title: Text(
                                            '${metric.itemName} (Q${metric.quadrant})'),
                                        subtitle: Text(
                                          '${metric.estimatedDaysRemaining.toStringAsFixed(1)} days left',
                                          style: TextStyle(
                                            color:
                                                metric.stockStatus == 'Critical'
                                                    ? AppTheme.criticalAlert
                                                    : AppTheme.lowStockAlert,
                                          ),
                                        ),
                                      )),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),

                        // Recent Scans
                        Text(
                          'Recent Scans',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 8),
                        if (!_isOnline)
                          const Text(
                            'No data — backend is offline.',
                            style: TextStyle(color: AppTheme.textSecondary),
                          )
                        else if (_scans.isEmpty)
                          const Text('No scans recorded yet.')
                        else
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _scans.length,
                            itemBuilder: (context, index) {
                              final scan = _scans[index];
                              return DetectionCard(
                                label: scan.label,
                                confidence: scan.confidence,
                                timestamp: scan.timestamp,
                              );
                            },
                          ),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(
      String title, String value, IconData icon, Color color) {
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
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
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
