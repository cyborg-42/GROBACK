// ignore: depend_on_referenced_packages
import 'dart:ui' show Color;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Singleton wrapper around flutter_local_notifications.
/// Call [NotificationService.instance.init()] once at app startup,
/// then use [showDepletionAlert] or [showLowStockAlert] anywhere in the app.
class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  // Android notification channel (required for Android 8+)
  static const _channelId   = 'groback_stock_alerts';
  static const _channelName = 'Stock Alerts';
  static const _channelDesc = 'Notifies when a shelf quadrant runs out of stock';

  // Notification IDs: depleted alerts use IDs 10-14, low/critical use 1-4.
  // This means repeated alerts for the same quadrant replace the previous one.
  static int _depletionId(int quadrant) => 10 + quadrant;
  static int _lowStockId(int quadrant)  => quadrant;

  /// Must be called once before showing any notification.
  /// Safe to call multiple times — subsequent calls are no-ops.
  Future<void> init() async {
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const darwinSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: darwinSettings,
      macOS: darwinSettings,
    );

    await _plugin.initialize(initSettings);

    // Create the Android notification channel (silently ignored on older OS)
    const channel = AndroidNotificationChannel(
      _channelId,
      _channelName,
      description: _channelDesc,
      importance: Importance.high,
      playSound: true,
    );

    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  /// Heads-up notification when a quadrant weight reaches exactly 0.
  Future<void> showDepletionAlert({
    required String itemName,
    required int quadrant,
  }) async {
    final androidDetails = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: _channelDesc,
      importance: Importance.high,
      priority: Priority.high,
      ticker: 'Stock depleted',
      color: const Color(0xFFE53935), // red
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
      macOS: iosDetails,
    );

    await _plugin.show(
      _depletionId(quadrant),
      '🛒 Restock Needed — $itemName',
      '$itemName in Quadrant $quadrant is fully depleted. Please restock now.',
      details,
    );
  }

  /// Softer notification for low/critical stock (weight > 0 but below threshold).
  Future<void> showLowStockAlert({
    required String itemName,
    required int quadrant,
    required String status,
    required double weightG,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: _channelDesc,
      importance: Importance.defaultImportance,
      priority: Priority.defaultPriority,
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: false,
      presentSound: false,
    );

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
      macOS: iosDetails,
    );

    await _plugin.show(
      _lowStockId(quadrant),
      '⚠️ $status — $itemName',
      '$itemName in Quadrant $quadrant is running low '
      '(${weightG.toStringAsFixed(0)} g remaining).',
      details,
    );
  }
}
