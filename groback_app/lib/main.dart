import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'navigation/bottom_navigation.dart';
import 'services/notification_service.dart';

void main() async {
  // Required before any async work before runApp
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize local notifications and create the Android channel
  await NotificationService.instance.init();

  runApp(const GroBackApp());
}

class GroBackApp extends StatelessWidget {
  const GroBackApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GroBack - Smart Shelf Monitor',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const BottomNavigation(),
    );
  }
}
