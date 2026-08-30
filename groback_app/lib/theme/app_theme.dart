import 'package:flutter/material.dart';

class AppTheme {
  // Color palette
  static const Color forestEmerald = Color(0xFF2E7D32); // Primary
  static const Color mintLeaf = Color(0xFF66BB6A); // Secondary
  static const Color darkGreen = Color(0xFF1B5E20); // Dark
  static const Color background = Color(0xFFF5F7F5); // Background
  static const Color card = Color(0xFFFFFFFF); // Card
  static const Color lowStockAlert = Color(0xFFFF9800); // Low Stock Alert
  static const Color criticalAlert = Color(0xFFE53935); // Critical Alert

  // Theme data
  static final ThemeData lightTheme = ThemeData(
    brightness: Brightness.light,
    primaryColor: forestEmerald,
    colorScheme: ColorScheme.light(
      primary: forestEmerald,
      secondary: mintLeaf,
      background: background,
    ),
    scaffoldBackgroundColor: background,
    appBarTheme: const AppBarTheme(
      backgroundColor: forestEmerald,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
    cardTheme: CardTheme(
      color: card,
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: forestEmerald,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: card,
      indicatorColor: forestEmerald.withOpacity(0.2),
      labelTextStyle: MaterialStateProperty.all(
        const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    ),
  );
}