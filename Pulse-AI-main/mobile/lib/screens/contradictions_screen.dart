import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/contradiction_card.dart';
import '../services/api_services.dart';

class ContradictionsScreen extends StatefulWidget {
  const ContradictionsScreen({super.key});

  @override
  State<ContradictionsScreen> createState() => _ContradictionsScreenState();
}

class _ContradictionsScreenState extends State<ContradictionsScreen>
    with TickerProviderStateMixin {
  String activeFilter = 'all';

  // Live data
  List<Map<String, dynamic>> _contradictions = [];
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
    if (_runId == null) {
      final args = ModalRoute.of(context)?.settings.arguments as Map?;
      _runId = args?['run_id'] as String?;
      if (_runId != null) {
        _fetchContradictions(_runId!);
      } else {
        setState(() {
          _loading = false;
          _error = 'No run_id provided';
        });
      }
    }
  }

  Future<void> _fetchContradictions(String runId) async {
    try {
      final data = await ApiService.getContradictions(runId);
      if (!mounted) return;
      final raw =
          (data['contradictions'] as List).cast<Map<String, dynamic>>();
      setState(() {
        _contradictions = _mapBackendContradictions(raw);
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

  /// Adapt backend Contradiction schema to the existing ContradictionCard
  /// widget contract. Backend fields:
  ///   conflict_id, metric, region, source_a (src_id), source_b (src_id),
  ///   value_a, value_b, status, chosen_source, rationale, confidence.
  /// UI expects:
  ///   id, title, source_a: {name, value, age_hours, credibility},
  ///   source_b: same, resolution, winner ('source_a'|'source_b'|'both'|null),
  ///   winner_label, rationale.
  List<Map<String, dynamic>> _mapBackendContradictions(
    List<Map<String, dynamic>> raw,
  ) {
    return raw.map((r) {
      final status = r['status'] as String? ?? 'resolved';
      // backend uses src_ids; UI wants a human-ish name + age/credibility hints
      final srcA = (r['source_a'] ?? '').toString();
      final srcB = (r['source_b'] ?? '').toString();
      String? winner;
      String? winnerLabel;
      if (status == 'resolved') {
        final chosen = (r['chosen_source'] ?? '').toString();
        winner = (chosen == srcA) ? 'source_a' : 'source_b';
        winnerLabel = chosen.isEmpty ? null : chosen;
      } else if (status == 'not_a_conflict') {
        winner = 'both';
        winnerLabel = 'Both true';
      } else {
        winner = null;
        winnerLabel = null;
      }
      return {
        'id': r['conflict_id'] ?? '',
        'title': r['metric'] ?? '',
        'source_a': {
          'name': srcA,
          'value': (r['value_a'] ?? '').toString(),
          'age_hours': 0,
          'credibility': 0.0,
        },
        'source_b': {
          'name': srcB,
          'value': (r['value_b'] ?? '').toString(),
          'age_hours': 0,
          'credibility': 0.0,
        },
        'resolution': status,
        'winner': winner,
        'winner_label': winnerLabel,
        'rationale': r['rationale'] ?? '',
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

  List<Map<String, dynamic>> get filteredContradictions {
    if (activeFilter == 'all') return _contradictions;
    return _contradictions
        .where((c) => c['resolution'] == activeFilter)
        .toList();
  }

  void _onFilterChanged(String filter) {
    setState(() {
      activeFilter = filter;
      for (var controller in _cardControllers.values) {
        controller.dispose();
      }
      _cardControllers.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final String runId = _runId ?? '';
    final items = filteredContradictions;
    final nhrCount = _contradictions
        .where((c) => c['resolution'] == 'needs_human_review')
        .length;

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
              "Contradictions",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
                fontSize: 17,
              ),
            ),
            Text(
              _loading
                  ? "Loading…"
                  : _error != null
                      ? "Could not load"
                      : "${_contradictions.length} conflicts detected · $nhrCount need${nhrCount == 1 ? 's' : ''} review",
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
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      _error!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontFamily: 'Poppins',
                        fontSize: 13,
                        color: AppColors.error,
                      ),
                    ),
                  ),
                )
              : AnimatedBuilder(
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
                      _buildFilterChips(),
                      Expanded(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.only(
                              left: 16, right: 16, top: 12, bottom: 8),
                          child: Column(
                            children: List.generate(items.length, (index) {
                              final item = items[index];
                              final controller =
                                  _getCardController(item['id'], index);

                              return AnimatedBuilder(
                                animation: controller,
                                builder: (context, child) {
                                  final fade =
                                      Tween<double>(begin: 0.0, end: 1.0)
                                          .animate(
                                    CurvedAnimation(
                                        parent: controller,
                                        curve: Curves.easeOut),
                                  );
                                  final slide =
                                      Tween<double>(begin: 20.0, end: 0.0)
                                          .animate(
                                    CurvedAnimation(
                                        parent: controller,
                                        curve: Curves.easeOut),
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
                                  padding:
                                      const EdgeInsets.only(bottom: 12.0),
                                  child: ContradictionCard(
                                    id: item['id'],
                                    title: item['title'],
                                    sourceA: Map<String, dynamic>.from(
                                        item['source_a']),
                                    sourceB: Map<String, dynamic>.from(
                                        item['source_b']),
                                    resolution: item['resolution'],
                                    winner: item['winner'],
                                    winnerLabel: item['winner_label'],
                                    rationale: item['rationale'],
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
          Expanded(
            child: Text(
              "ConflictResolver Agent: complete  ·  2 resolved  ·  1 escalated",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                fontSize: 12,
                color: AppColors.success,
              ),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    final filters = [
      {'label': 'All (3)', 'value': 'all'},
      {'label': 'Resolved (2)', 'value': 'resolved'},
      {'label': 'Needs Review (1)', 'value': 'needs_human_review'},
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
              RouteNames.actionPlan,
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
            "View Action Plan  →",
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
