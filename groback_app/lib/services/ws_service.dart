import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'api_service.dart';

/// Singleton WebSocket service.
/// Connects to the backend /ws endpoint and exposes a broadcast stream.
/// Reconnects automatically on disconnect.
class WsService {
  WsService._();
  static final WsService instance = WsService._();

  WebSocketChannel? _channel;
  final _controller = StreamController<Map<String, dynamic>>.broadcast();
  bool _disposed = false;
  Timer? _reconnectTimer;

  Stream<Map<String, dynamic>> get stream => _controller.stream;

  void connect() {
    _disposed = false;
    _openChannel();
  }

  void _openChannel() {
    if (_disposed) return;
    try {
      // Strip any trailing fragment (#) that would break the WS handshake
      final base = ApiService.baseUrl
          .replaceFirst(RegExp(r'^http'), 'ws')
          .replaceAll(RegExp(r'#.*$'), '');
      final uri = Uri.parse('$base/ws');

      _channel = WebSocketChannel.connect(uri);

      // ready completes once the handshake succeeds; errors here are caught below
      _channel!.ready.then((_) {
        _channel!.stream.listen(
          (raw) {
            try {
              final data = jsonDecode(raw as String) as Map<String, dynamic>;
              if (!_controller.isClosed) _controller.add(data);
            } catch (_) {}
          },
          onDone: _scheduleReconnect,
          onError: (_) => _scheduleReconnect(),
          cancelOnError: true,
        );
      }).catchError((Object _) { _scheduleReconnect(); });
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 3), _openChannel);
  }

  void dispose() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _controller.close();
  }
}
