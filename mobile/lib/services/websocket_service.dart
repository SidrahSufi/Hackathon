import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_config.dart';

/// pulseAI — WebSocket Service
/// Manages real-time agent trace events.
class WebSocketService {
  /// Connects to the trace events stream for a specific run.
  static WebSocketChannel connect(String runId) {
    final uri = Uri.parse(
      '${ApiConfig.wsBaseUrl}/api/scenarios/runs/$runId/events',
    );
    return WebSocketChannel.connect(uri);
  }

  /// Helper to determine if an event signifies the end of the trace.
  static bool isLastEvent(Map<String, dynamic> event) {
    final agent = event['agent']?.toString().toLowerCase() ?? '';
    final kind = event['kind']?.toString() ?? '';

    // Backend emits a final pipeline_done event when everything finishes.
    if (kind == 'pipeline_done') return true;

    // Or: outcome resource ready means the chain is complete.
    if (kind == 'resource_ready' || kind == 'resource_ready_replay') {
      final payload = event['payload'] as Map<String, dynamic>?;
      if (payload != null && payload['resource'] == 'outcome') return true;
    }

    // Backwards-compatible with older simulated demo events.
    final message = event['message']?.toString() ?? '';
    if (kind == 'completed') {
      if (agent == 'monitor') return true;
      if (agent == 'executor' && message.contains('A5')) return true;
    }
    return false;
  }
}
