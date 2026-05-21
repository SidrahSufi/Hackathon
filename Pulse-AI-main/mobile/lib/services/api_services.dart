import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_config.dart';

/// pulseAI — REST API client.
///
/// All calls hit the FastAPI backend (see backend/api/routes/scenarios.py).
/// Endpoints documented in repo README.
class ApiService {
  ApiService._();

  // ------------------------------------------------------------------
  // Run lifecycle
  // ------------------------------------------------------------------

  /// Kick off a new pipeline run on the backend.
  /// Returns the server-generated run_id.
  static Future<String> startRun({
    String scenarioId = 'zarapk_regional_v1',
    String seedRegion = 'lahore',
  }) async {
    final uri = Uri.parse('${ApiConfig.httpBaseUrl}/api/scenarios/run');
    final resp = await http.post(
      uri,
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'scenario_id': scenarioId,
        'seed_region': seedRegion,
      }),
    );
    if (resp.statusCode != 200) {
      throw ApiException(
        'startRun failed: ${resp.statusCode} ${resp.body}',
      );
    }
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    return body['run_id'] as String;
  }

  /// Fetch high-level status: running / completed / failed, current phase,
  /// detected region, list of resources ready.
  static Future<Map<String, dynamic>> getRunStatus(String runId) async {
    final uri = Uri.parse('${ApiConfig.httpBaseUrl}/api/scenarios/runs/$runId');
    final resp = await http.get(uri);
    if (resp.statusCode != 200) {
      throw ApiException(
        'getRunStatus failed: ${resp.statusCode} ${resp.body}',
      );
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ------------------------------------------------------------------
  // Per-stage resource fetchers
  //
  // Each one polls until the JSON file exists on the backend
  // (sub-resource endpoints return 202 when the file isn't ready yet).
  // ------------------------------------------------------------------

  static Future<Map<String, dynamic>> getSources(String runId) =>
      _pollResource(runId, 'sources');

  static Future<Map<String, dynamic>> getInsights(String runId) =>
      _pollResource(runId, 'insights');

  static Future<Map<String, dynamic>> getContradictions(String runId) =>
      _pollResource(runId, 'contradictions');

  static Future<Map<String, dynamic>> getPlan(String runId) =>
      _pollResource(runId, 'plan');

  static Future<Map<String, dynamic>> getExecution(String runId) =>
      _pollResource(runId, 'execution');

  static Future<Map<String, dynamic>> getMonitor(String runId) =>
      _pollResource(runId, 'monitor');

  static Future<Map<String, dynamic>> getOutcome(String runId) =>
      _pollResource(runId, 'outcome');

  // ------------------------------------------------------------------
  // Internals
  // ------------------------------------------------------------------

  static Future<Map<String, dynamic>> _pollResource(
    String runId,
    String resource, {
    Duration timeout = const Duration(seconds: 90),
  }) async {
    final uri = Uri.parse(
      '${ApiConfig.httpBaseUrl}/api/scenarios/runs/$runId/$resource',
    );

    final deadline = DateTime.now().add(timeout);
    while (DateTime.now().isBefore(deadline)) {
      final resp = await http.get(uri);
      if (resp.statusCode == 200) {
        return jsonDecode(resp.body) as Map<String, dynamic>;
      } else if (resp.statusCode == 202) {
        // Not ready yet — back off and try again
        await Future.delayed(ApiConfig.pollInterval);
        continue;
      } else {
        throw ApiException(
          '$resource fetch failed: ${resp.statusCode} ${resp.body}',
        );
      }
    }
    throw ApiException('Timed out waiting for $resource on run $runId');
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}
