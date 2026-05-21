import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/insight_card.dart';
import '../services/api_services.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen>
    with TickerProviderStateMixin {
  String activeFilter = 'all';

  // Live data loaded from backend
  List<Map<String, dynamic>> _insights = [];
  String? _detectedRegion;
  bool _loading = true;
  String? _error;
  String? _runId;

  late AnimationController _screenController;
  late Animation<double> _screenFade;
  late Animation<double> _screenSlide;

  final Map<String, AnimationController> _cardControllers = {};

  @override
  void initState() {
    super.initState();

    _screenController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _screenFade = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _screenController, curve: Curves.easeOut),
    );
    _screenSlide = Tween<double>(begin: 20.0, end: 0.0).animate(
      CurvedAnimation(parent: _screenController, curve: Curves.easeOut),
    );

    _screenController.forward();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Read run_id from route args once, then fetch insights from backend
    if (_runId == null) {
      final args = ModalRoute.of(context)?.settings.arguments as Map?;
      _runId = args?['run_id'] as String?;
      if (_runId != null) {
        _fetchInsights(_runId!);
      } else {
        setState(() {
          _loading = false;
          _error = 'No run_id provided';
        });
      }
    }
  }

  Future<void> _fetchInsights(String runId) async {
    try {
      final data = await ApiService.getInsights(runId);
      if (!mounted) return;
      setState(() {
        _detectedRegion = data['detected_outlier_region'] as String?;
        _insights = _mapBackendInsights(
          (data['insights'] as List).cast<Map<String, dynamic>>(),
        );
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  /// Adapt backend Insight schema -> InsightCard widget props.
  /// Backend fields: insight_id, title, severity (info|low|medium|high|critical),
  ///                 confidence, region, evidence_refs, metrics, rationale.
  List<Map<String, dynamic>> _mapBackendInsights(List<Map<String, dynamic>> raw) {
    return raw.map((r) {
      return {
        'id': r['insight_id'] ?? r['id'] ?? '',
        'title': r['title'] ?? '',
        'detail': r['rationale'] ?? '',
        'severity': r['severity'] ?? 'info',
        'confidence': (r['confidence'] is num)
            ? (r['confidence'] as num).toDouble()
            : 0.0,
        'evidence_refs': List<String>.from(r['evidence_refs'] ?? const []),
      };
    }).toList();
  }

  @override
  void dispose() {
    _screenController.dispose();
    for (var controller in _cardControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  AnimationController _getCardController(String id, int index) {
    if (!_cardControllers.containsKey(id)) {
      final controller = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 300),
      );
      _cardControllers[id] = controller;

      Future.delayed(Duration(milliseconds: index * 150), () {
        if (mounted) {
          controller.forward();
        }
      });
    }
    return _cardControllers[id]!;
  }

  List<Map<String, dynamic>> get filteredInsights {
    final sorted = [..._insights]..sort((a, b) {
        const order = {
          'critical': 0,
          'high': 1,
          'medium': 2,
          'low': 3,
          'info': 4,
        };
        return (order[a['severity']] ?? 99)
            .compareTo(order[b['severity']] ?? 99);
      });
    if (activeFilter == 'all') return sorted;
    return sorted.where((i) => i['severity'] == activeFilter).toList();
  }

  void _onFilterChanged(String filter) {
    setState(() {
      activeFilter = filter;
      // Reset animations for the new filtered list
      for (var controller in _cardControllers.values) {
        controller.dispose();
      }
      _cardControllers.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final String runId = _runId ?? '';
    final insights = filteredInsights;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Insights",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
                fontSize: 17,
              ),
            ),
            Text(
              _loading
                  ? "Loading insights…"
                  : _error != null
                      ? "Could not load"
                      : "${insights.length} findings · ${_detectedRegion ?? '—'} flagged",
              style: const TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 0),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorState()
              : _buildLoadedBody(runId, insights),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline,
                color: AppColors.error, size: 40),
            const SizedBox(height: 12),
            Text(
              _error ?? 'Unknown error',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontFamily: 'Poppins',
                fontSize: 13,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadedBody(String runId, List<Map<String, dynamic>> insights) {
    return AnimatedBuilder(
      animation: _screenController,
      builder: (context, child) {
        return Opacity(
          opacity: _screenFade.value,
          child: Transform.translate(
            offset: Offset(0, _screenSlide.value),
            child: child,
          ),
        );
      },
      child: Column(
        children: [
          _buildAgentStatusBanner(),
          _buildKeyInsightsSummary(),
          _buildFilterChips(insights),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.only(
                  left: 16, right: 16, top: 12, bottom: 8),
              child: Column(
                children: List.generate(insights.length, (index) {
                  final item = insights[index];
                  final controller = _getCardController(item['id'], index);

                  return AnimatedBuilder(
                    animation: controller,
                    builder: (context, child) {
                      final fade =
                          Tween<double>(begin: 0.0, end: 1.0).animate(
                        CurvedAnimation(
                            parent: controller, curve: Curves.easeOut),
                      );
                      final slide =
                          Tween<double>(begin: 20.0, end: 0.0).animate(
                        CurvedAnimation(
                            parent: controller, curve: Curves.easeOut),
                      );
                      return Opacity(
                        opacity: fade.value,
                        child: Transform.translate(
                          offset: Offset(0, slide.value),
                          child: child,
                        ),
                      );
                    },
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: InsightCard(
                        id: item['id'],
                        title: item['title'],
                        detail: item['detail'],
                        severity: item['severity'],
                        confidence: item['confidence'],
                        evidenceRefs:
                            List<String>.from(item['evidence_refs']),
                      ),
                    ),
                  );
                }),
              ),
            ),
          ),
          _buildPinnedButton(runId),
        ],
      ),
    );
  }

  Widget _buildAgentStatusBanner() {
    return Container(
      margin: const EdgeInsets.only(left: 16, right: 16, top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5EE),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 16,
            color: AppColors.success,
          ),
          SizedBox(width: 8),
          Text(
            "Insight Agent: complete  ·  94% avg confidence",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 13,
              color: AppColors.success,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKeyInsightsSummary() {
    final region = _detectedRegion ?? 'the outlier region';
    final critical = _insights.where((i) => i['severity'] == 'critical').length;
    final high = _insights.where((i) => i['severity'] == 'high').length;
    final summary = critical + high > 0
        ? "The decline in $region orders is a statistically significant outlier; "
            "$critical critical and $high high-severity insights surfaced. "
            "Other regions remain stable."
        : "No critical issues surfaced. Other regions stable.";
    return Container(
      margin: const EdgeInsets.only(left: 16, right: 16, top: 16),
      padding: const EdgeInsets.all(16),
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.auto_awesome, size: 16, color: AppColors.primaryBlue),
              SizedBox(width: 8),
              Text(
                "Executive Summary",
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w500,
                  fontSize: 14,
                  color: AppColors.primaryDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            summary,
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w400,
              fontSize: 13,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips(List<Map<String, dynamic>> currentInsights) {
    final byLevel = <String, int>{};
    for (final i in _insights) {
      final s = (i['severity'] ?? 'info') as String;
      byLevel[s] = (byLevel[s] ?? 0) + 1;
    }
    final filters = [
      {'label': 'All (${_insights.length})', 'value': 'all'},
      {'label': 'Critical (${byLevel['critical'] ?? 0})', 'value': 'critical'},
      {'label': 'High (${byLevel['high'] ?? 0})', 'value': 'high'},
      {'label': 'Medium (${byLevel['medium'] ?? 0})', 'value': 'medium'},
      {'label': 'Low (${byLevel['low'] ?? 0})', 'value': 'low'},
    ];

    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      width: double.infinity,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        clipBehavior: Clip.none,
        child: Row(
          children: filters.map((f) {
            final isActive = activeFilter == f['value'];
            return Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: GestureDetector(
                onTap: () => _onFilterChanged(f['value']!),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: isActive ? AppColors.primaryBlue : AppColors.surface,
                    borderRadius: BorderRadius.circular(20),
                    border: isActive
                        ? null
                        : Border.all(color: AppColors.border, width: 0.5),
                  ),
                  child: Text(
                    f['label']!,
                    style: TextStyle(
                      fontFamily: 'Poppins',
                      fontWeight: isActive ? FontWeight.w500 : FontWeight.w400,
                      fontSize: 12,
                      color: isActive ? Colors.white : AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildPinnedButton(String runId) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.background,
        border: Border(
          top: BorderSide(color: AppColors.border, width: 0.5),
        ),
      ),
      child: SizedBox(
        width: double.infinity,
        height: 52,
        child: ElevatedButton(
          onPressed: () {
            Navigator.pushNamed(
              context,
              RouteNames.contradictions,
              arguments: {'run_id': runId},
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primaryBlue,
            foregroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: const Text(
            "View Contradictions  →",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 15,
            ),
          ),
        ),
      ),
    );
  }
}
