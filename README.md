# GroBack AI-IoT Smart Shelf System

AI-IoT Hybrid Framework for Proactive Grocery Inventory Management, Visual Item Recognition, and Consumption Analytics.

## Project Structure

- `backend/` - FastAPI server with SQLite database
- `groback_app/` - Flutter mobile application

## Backend Setup (FastAPI)

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pillow tensorflow numpy
   ```

   Note: For TensorFlow, you might want to install the appropriate version for your system (e.g., `tensorflow` or `tensorflow-macos` or `tensorflow-cpu`).

### Running the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- Local: http://127.0.0.1:8000
- For Android Emulator: Use `10.0.2.2:8000` (this is handled automatically by the Flutter app)
- For physical Android device on same network: Use your machine's IP address (e.g., `192.168.x.x:8000`)

### API Documentation
Once the server is running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Frontend Setup (Flutter)

### Prerequisites
- Flutter SDK (version 3.0.0+)
- Dart SDK
- Android Studio or VS Code with Flutter extensions
- Android Emulator or physical Android device for testing

### Getting Dependencies
1. Navigate to the flutter app directory:
   ```bash
   cd groback_app
   ```

2. Fetch dependencies:
   ```bash
   flutter pub get
   ```

### Running the App
#### On Android Emulator
1. Start an Android emulator (via Android Studio or command line)
2. Run:
   ```bash
   flutter run
   ```

#### On Physical Android Device
1. Enable USB debugging on your device
2. Connect via USB
3. Run:
   ```bash
   flutter run
   ```

#### On Web (Chrome)
```bash
flutter run -d chrome
```

#### On Windows (Desktop)
```bash
flutter run -d windows
```

### Note on Backend Connection
The Flutter app automatically selects the correct backend URL:
- `http://10.0.2.2:8000` when running on Android Emulator/Device
- `http://127.0.0.1:8000` when running on Web or Desktop (Windows/macOS/Linux)

If you are running the Flutter app on a physical device and the backend is on your development machine, ensure both are on the same Wi-Fi network and use your machine's local IP address in the `baseUrl` getter in `lib/services/api_service.dart` if needed (though the current code uses localhost for non-Android, which won't work for physical devices). For physical device testing, you may want to adjust the `baseUrl` to point to your machine's IP (e.g., `return "http://192.168.1.100:8000";`).

## Demo Instructions

To see the system in action:

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the Flutter app (on emulator or device):
   ```bash
   cd groback_app
   flutter run
   ```

3. In the app:
   - Go to the **Inventory** screen to see the 4 quadrants with simulated weights
   - Use the buttons (Q+100g, Q-100g, Q4 Empty) to simulate weight changes
   - Go to the **Scan** screen and use the fruit buttons (Apple, Banana, Orange, Carrot) to simulate scanning
   - Observe the real-time updates in the **Home** screen (recent scans, depletion alerts)
   - Check the **Analytics** screen for consumption predictions and shopping list

## Troubleshooting

- **Backend Connection Issues**: Ensure the backend is running and accessible from the device/emulator. Check firewall settings.
- **Port Already in Use**: If port 8000 is busy, change the port in the uvicorn command and update the `baseUrl` in `api_service.dart` accordingly.
- **Flutter Build Issues**: Run `flutter clean` and then `flutter pub get` again.
- **TensorFlow Import Errors**: Make sure TensorFlow is installed correctly for your platform.

## Future Enhancements

- Replace the color-based mock model with a trained CNN for actual item recognition
- Integrate real ESP32 firmware for weight sensing and camera capture
- Add user authentication and synchronization with cloud backend
- Enhance analytics with more sophisticated time-series forecasting
- Add historical data visualization and export capabilities

---
*GroBack - Smart Shelf Monitor*