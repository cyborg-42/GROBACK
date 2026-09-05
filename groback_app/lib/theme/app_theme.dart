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

  // Aliases and text tokens
  static const Color primary = forestEmerald;
  static const Color primaryLight = mintLeaf;
  static const Color primaryDark = darkGreen;
  static const Color accentOrange = lowStockAlert;
  static const Color accentRed = criticalAlert;
  static const Color textPrimary = Color(0xFF1E293B);
  static const Color textSecondary = Color(0xFF64748B);

  // Theme data
  static final ThemeData lightTheme = ThemeData(
    brightness: Brightness.light,
    primaryColor: forestEmerald,
    colorScheme: const ColorScheme.light(
      primary: forestEmerald,
      secondary: mintLeaf,
      surface: card,
    ),
    scaffoldBackgroundColor: background,
    appBarTheme: const AppBarTheme(
      backgroundColor: forestEmerald,
      foregroundColor: Colors.white,
      elevation: 0,
    ),
    cardTheme: CardThemeData(
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
      indicatorColor: forestEmerald.withValues(alpha: 0.2),
      labelTextStyle: WidgetStateProperty.all(
        const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    ),
  );
}