/// pulseAI — Backend connection config.
///
/// Edit ONE place to point the app at a different backend.
/// Local dev:  http://10.0.2.2:8080  (Android emulator) or  http://localhost:8080
/// Cloud Run:  https://pulseai-backend-XXXXXX-uc.a.run.app
class ApiConfig {
  ApiConfig._();

  /// HTTP base URL (no trailing slash).
  // static const String httpBaseUrl = 'http://10.0.2.2:8080';        // Android emulator
  // static const String httpBaseUrl = 'http://localhost:8080';        // iOS simulator
  // static const String httpBaseUrl = 'http://192.168.x.x:8080';     // Real device
  static const String httpBaseUrl =
      'https://pulse-ai-716770251318.us-central1.run.app'; // ✅ Cloud Run

  /// WebSocket base URL
  // static const String wsBaseUrl = 'ws://10.0.2.2:8080';            // Android emulator
  // static const String wsBaseUrl = 'ws://localhost:8080';            // iOS simulator
  // static const String wsBaseUrl = 'ws://192.168.x.x:8080';         // Real device
  static const String wsBaseUrl =
      'wss://pulse-ai-716770251318.us-central1.run.app'; // ✅ Cloud Run

  /// Default seed region used when no explicit choice is made on Home screen.
  static const String defaultSeedRegion = 'lahore';

  /// Total timeout for the pipeline to produce its final outcome.
  static const Duration pipelineTimeout = Duration(seconds: 90);

  /// Polling interval when waiting on a not-yet-ready resource.
  static const Duration pollInterval = Duration(milliseconds: 600);
}
