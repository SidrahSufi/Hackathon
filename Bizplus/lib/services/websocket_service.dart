import 'package:web_socket_channel/web_socket_channel.dart';

/// BizPulse — WebSocket Service
/// Manages real-time agent trace events.
class WebSocketService {
  static const String baseUrl = 'ws://BACKEND_URL/api/scenarios/runs';

  /// Connects to the trace events stream for a specific run.
  static WebSocketChannel connect(String runId) {
    final uri = Uri.parse('$baseUrl/$runId/events');
    return WebSocketChannel.connect(uri);
  }

  /// Helper to determine if an event signifies the end of the trace.
  static bool isLastEvent(Map<String, dynamic> event) {
    // Logic: If Monitor or Executor completes the final planned action
    final agent = event['agent'];
    final kind = event['kind'];
    final message = event['message']?.toString() ?? '';

    if (kind == 'completed') {
      if (agent == 'Monitor') return true;
      if (agent == 'Executor' && message.contains('A5')) return true;
    }
    return false;
  }
}
