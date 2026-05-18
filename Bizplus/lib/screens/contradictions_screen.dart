import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/contradiction_card.dart';

// DEMO DATA — remove when backend ready
final List<Map<String, dynamic>> demoContradictions = [
  {
    'id': 'c-1',
    'title': 'Lahore sales growth: conflicting sources',
    'source_a': {
      'name': 'PDF Sales Report',
      'value': '+5% YoY',
      'age_hours': 720,
      'credibility': 0.60
    },
    'source_b': {
      'name': 'POS CSV (fresh)',
      'value': '−25% last 30d',
      'age_hours': 2,
      'credibility': 0.95
    },
    'resolution': 'resolved',
    'winner': 'source_b',
    'winner_label': 'POS CSV',
    'rationale':
        'POS data is 2 hours fresh. PDF is 30 days old and predates competitor entry. Recency wins.',
  },
  {
    'id': 'c-2',
    'title': 'Marketing budget vs actual reach',
    'source_a': {
      'name': 'Marketing Dashboard',
      'value': 'Full budget active',
      'age_hours': 12,
      'credibility': 0.85
    },
    'source_b': {
      'name': 'Analytics JSON',
      'value': 'Reach −40% in Lahore',
      'age_hours': 24,
      'credibility': 0.88
    },
    'resolution': 'resolved',
    'winner': 'both',
    'winner_label': 'Both true',
    'rationale':
        'Both are true simultaneously — spend going out but delivery is broken. Campaign delivery problem, not a data conflict.',
  },
  {
    'id': 'c-3',
    'title': 'Competitor pricing vs ZaraPK',
    'source_a': {
      'name': 'News Article',
      'value': 'Competitor 30% cheaper',
      'age_hours': 168,
      'credibility': 0.72
    },
    'source_b': {
      'name': 'Pricing Blog',
      'value': 'Competitor prices similar',
      'age_hours': 72,
      'credibility': 0.30
    },
    'resolution': 'needs_human_review',
    'winner': null,
    'winner_label': null,
    'rationale':
        'Sources disagree and blog is low credibility (0.30). Cannot confirm pricing gap. Human review required.',
  },
];

class ContradictionsScreen extends StatefulWidget {
  const ContradictionsScreen({super.key});

  @override
  State<ContradictionsScreen> createState() => _ContradictionsScreenState();
}

class _ContradictionsScreenState extends State<ContradictionsScreen>
    with TickerProviderStateMixin {
  String activeFilter = 'all';

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
    if (activeFilter == 'all') return demoContradictions;
    return demoContradictions
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
    final args = ModalRoute.of(context)?.settings.arguments as Map?;
    final String runId = args?['run_id'] ?? 'demo-run-001';

    final items = filteredContradictions;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Contradictions",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
                fontSize: 17,
              ),
            ),
            Text(
              "3 conflicts detected · 1 needs review",
              style: TextStyle(
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
      body: AnimatedBuilder(
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
                        padding: const EdgeInsets.only(bottom: 12.0),
                        child: ContradictionCard(
                          id: item['id'],
                          title: item['title'],
                          sourceA: Map<String, dynamic>.from(item['source_a']),
                          sourceB: Map<String, dynamic>.from(item['source_b']),
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
