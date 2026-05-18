import '../widgets/bottom_nav_bar.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/action_dag_card.dart';

/// S5 — Action Plan Screen
/// Shows the 5-action DAG with budget summary, feasibility badge,
/// and a chained execution animation.
/// Owner: Shahzar (Mobile-2)
class ActionPlanScreen extends StatefulWidget {
  const ActionPlanScreen({super.key});

  @override
  State<ActionPlanScreen> createState() => _ActionPlanScreenState();
}

class _ActionPlanScreenState extends State<ActionPlanScreen>
    with TickerProviderStateMixin {
  // ───────────────────────── state ─────────────────────────

  bool _isExecuting = false;
  bool _isComplete = false;

  /// Status map for all 5 actions in the DAG.
  final Map<String, String> _statuses = {
    'A1': 'pending',
    'A2': 'pending',
    'A3': 'pending',
    'A4': 'pending',
    'A5': 'pending',
  };

  /// Tracks whether the budget bar should show completion color.
  bool _budgetBarComplete = false;

  // ───────────────────────── animation controllers ─────────
  late final AnimationController _staggerController;
  late final List<Animation<double>> _fadeAnimations;
  late final List<Animation<Offset>> _slideAnimations;

  static const int _sectionCount = 4; // budget, feasibility, dag, button

  // ───────────────────────── demo data ─────────────────────
  // DEMO DATA — remove when backend ready
  final Map<String, dynamic> _demoPlan = const {
    'feasible': true,
    'budget_used': 720000,
    'budget_cap': 800000,
    'discount_pct': 18,
    'discount_max': 20,
    'projected_reach': 5200,
  };

  // DEMO DATA — remove when backend ready
  final List<Map<String, dynamic>> _actions = const [
    {
      'id': 'A1',
      'title': 'Diagnose SKUs + segments',
      'cost_pkr': 0,
      'latency_s': 30,
    },
    {
      'id': 'A2',
      'title': 'Notify regional leads',
      'cost_pkr': 0,
      'latency_s': 5,
    },
    {
      'id': 'A3',
      'title': 'Launch Lahore campaign',
      'cost_pkr': 720000,
      'latency_s': 12,
    },
    {
      'id': 'A4',
      'title': 'Update pricing + notifications',
      'cost_pkr': 0,
      'latency_s': 120,
    },
    {
      'id': 'A5',
      'title': 'Schedule 7-day monitor',
      'cost_pkr': 0,
      'latency_s': 1,
    },
  ];

  @override
  void initState() {
    super.initState();

    // Stagger entrance animations
    _staggerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300 + (_sectionCount - 1) * 100),
    );

    _fadeAnimations = List.generate(_sectionCount, (i) {
      final start = (i * 100) / (300 + (_sectionCount - 1) * 100);
      final end = (i * 100 + 300) / (300 + (_sectionCount - 1) * 100);
      return CurvedAnimation(
        parent: _staggerController,
        curve: Interval(
          start.clamp(0.0, 1.0),
          end.clamp(0.0, 1.0),
          curve: Curves.easeOut,
        ),
      );
    });

    _slideAnimations = List.generate(_sectionCount, (i) {
      final start = (i * 100) / (300 + (_sectionCount - 1) * 100);
      final end = (i * 100 + 300) / (300 + (_sectionCount - 1) * 100);
      return Tween<Offset>(
        begin: const Offset(0, 20),
        end: Offset.zero,
      ).animate(
        CurvedAnimation(
          parent: _staggerController,
          curve: Interval(
            start.clamp(0.0, 1.0),
            end.clamp(0.0, 1.0),
            curve: Curves.easeOut,
          ),
        ),
      );
    });

    _staggerController.forward();
  }

  @override
  void dispose() {
    _staggerController.dispose();
    super.dispose();
  }

  // ───────────────────────── run id ─────────────────────────
  String? get _runId {
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is String) return args;
    return 'r-demo-001'; // DEMO DATA — remove when backend ready
  }

  // ───────────────────────── execution chain ────────────────
  Future<void> _executeChain() async {
    setState(() => _isExecuting = true);

    // A1: running → done
    await Future.delayed(const Duration(milliseconds: 400));
    _setStatus('A1', 'running');
    await Future.delayed(const Duration(milliseconds: 1000));
    _setStatus('A1', 'done');

    // A2 + A3: running simultaneously
    await Future.delayed(const Duration(milliseconds: 300));
    _setStatus('A2', 'running');
    _setStatus('A3', 'running');
    await Future.delayed(const Duration(milliseconds: 900));
    _setStatus('A2', 'done');
    await Future.delayed(const Duration(milliseconds: 400));
    _setStatus('A3', 'done');
    setState(() => _budgetBarComplete = true);

    // A4: running → failed → retry → done
    await Future.delayed(const Duration(milliseconds: 300));
    _setStatus('A4', 'running');
    await Future.delayed(const Duration(milliseconds: 800));
    _setStatus('A4', 'failed');
    await Future.delayed(const Duration(milliseconds: 600));
    _setStatus('A4', 'retry');
    await Future.delayed(const Duration(milliseconds: 800));
    _setStatus('A4', 'done');

    // A5: running → done
    await Future.delayed(const Duration(milliseconds: 300));
    _setStatus('A5', 'running');
    await Future.delayed(const Duration(milliseconds: 600));
    _setStatus('A5', 'done');

    if (!mounted) return;
    setState(() {
      _isExecuting = false;
      _isComplete = true;
    });
  }

  void _setStatus(String actionId, String status) {
    if (!mounted) return;
    setState(() => _statuses[actionId] = status);
  }

  // ───────────────────────── build ──────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: _buildAppBar(),
      body: _buildBody(),
      bottomNavigationBar: const BottomNavBar(currentIndex: 1),
    );
  }

  // ─── AppBar ───────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: AppColors.background,
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new, size: 20),
        color: AppColors.primaryBlue,
        onPressed: () => Navigator.pop(context),
      ),
      title: Text(
        'Action Plan',
        style: GoogleFonts.poppins(
          fontWeight: FontWeight.w500,
          fontSize: 18,
          color: AppColors.primaryDark,
        ),
      ),
    );
  }

  // ─── Body ─────────────────────────────────────────────────
  Widget _buildBody() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // A — Budget Summary
          _animatedSection(0, _buildBudgetCard()),
          const SizedBox(height: 12),

          // B — Feasibility Badge
          _animatedSection(1, _buildFeasibilityBadge()),
          const SizedBox(height: 12),

          // C — DAG
          _animatedSection(2, _buildDagCard()),
          const SizedBox(height: 12),

          // D — Run button
          _animatedSection(3, _buildRunButton()),
        ],
      ),
    );
  }

  // ─── Animated section wrapper ─────────────────────────────
  Widget _animatedSection(int index, Widget child) {
    return AnimatedBuilder(
      animation: _staggerController,
      builder: (context, _) {
        return Transform.translate(
          offset: _slideAnimations[index].value,
          child: Opacity(opacity: _fadeAnimations[index].value, child: child),
        );
      },
    );
  }

  // ─── A. Budget Summary Card ───────────────────────────────
  Widget _buildBudgetCard() {
    final budgetUsed = _demoPlan['budget_used'] as int; // DEMO DATA
    final budgetCap = _demoPlan['budget_cap'] as int; // DEMO DATA
    final discountPct = _demoPlan['discount_pct'] as int; // DEMO DATA
    final discountMax = _demoPlan['discount_max'] as int; // DEMO DATA
    final reach = _demoPlan['projected_reach'] as int; // DEMO DATA
    final budgetFraction = budgetUsed / budgetCap;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Label
          Text(
            'BUDGET SUMMARY',
            style: GoogleFonts.poppins(
              fontSize: 11,
              letterSpacing: 0.5,
              fontWeight: FontWeight.w400,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 10),

          // Amount row
          Row(
            children: [
              Text(
                '${_formatNumber(budgetUsed)} PKR',
                style: GoogleFonts.poppins(
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                  color: AppColors.primaryBlue,
                ),
              ),
              const Spacer(),
              Text(
                'cap ${_formatNumber(budgetCap)} PKR',
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.w400,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Budget bar
          Container(
            height: 6,
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(20),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: budgetFraction.clamp(0.0, 1.0),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 500),
                curve: Curves.easeOut,
                decoration: BoxDecoration(
                  color: _budgetBarComplete
                      ? AppColors.primaryBlue
                      : AppColors.warning,
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),

          // Pills row
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _BudgetPill(label: 'Discount $discountPct% / max $discountMax%'),
              _BudgetPill(label: 'Reach ${_formatNumber(reach)} customers'),
            ],
          ),
        ],
      ),
    );
  }

  // ─── B. Feasibility Badge ─────────────────────────────────
  Widget _buildFeasibilityBadge() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.successTint,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.success, width: 0.5),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.check_circle_outline,
            size: 18,
            color: AppColors.success,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Plan is feasible — within budget and discount limits',
              style: GoogleFonts.poppins(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: AppColors.success,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── C. DAG Card ──────────────────────────────────────────
  Widget _buildDagCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Label
          Text(
            'EXECUTION CHAIN',
            style: GoogleFonts.poppins(
              fontSize: 11,
              letterSpacing: 0.5,
              fontWeight: FontWeight.w400,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 10),

          // ─── DAG Visual ────────────────────────────────────
          // Row 1: A1 centered
          Center(child: _dagNode('A1')),

          // Connector: two lines branching down to A2 and A3
          _branchConnector(),

          // Row 2: A2 + A3
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _dagNode('A2'),
              const SizedBox(width: 10),
              _dagNode('A3'),
            ],
          ),

          // Connector: single line offset right (under A3)
          _singleConnectorRight(),

          // Row 3: A4 centered
          Center(child: _dagNode('A4')),

          // Connector: single centered
          _singleConnector(),

          // Row 4: A5 centered
          Center(child: _dagNode('A5')),
        ],
      ),
    );
  }

  /// Builds an [ActionDagCard] for the given action ID.
  Widget _dagNode(String id) {
    final action = _actions.firstWhere((a) => a['id'] == id);
    return ActionDagCard(
      id: id,
      title: action['title'] as String,
      costPkr: action['cost_pkr'] as int,
      latencyS: action['latency_s'] as int,
      status: _statuses[id] ?? 'pending',
    );
  }

  /// Two vertical bars branching from A1 down to A2 and A3.
  Widget _branchConnector() {
    return SizedBox(
      height: 16,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(width: 2, height: 16, color: AppColors.border),
          const SizedBox(width: 80),
          Container(width: 2, height: 16, color: AppColors.border),
        ],
      ),
    );
  }

  /// Single vertical bar, offset right to align under A3.
  Widget _singleConnectorRight() {
    return SizedBox(
      height: 16,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(width: 80),
          Container(width: 2, height: 16, color: AppColors.border),
        ],
      ),
    );
  }

  /// Single vertical bar, centered.
  Widget _singleConnector() {
    return Center(
      child: Container(width: 2, height: 16, color: AppColors.border),
    );
  }

  // ─── D. Run Button ────────────────────────────────────────
  Widget _buildRunButton() {
    if (_isComplete) {
      return SizedBox(
        width: double.infinity,
        height: 52,
        child: ElevatedButton(
          onPressed: () {
            Navigator.pushNamed(
              context,
              RouteNames.liveTrace,
              arguments: _runId,
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.success,
            foregroundColor: AppColors.background,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: Text(
            'Plan Executed — View Live Trace →',
            style: GoogleFonts.poppins(
              fontWeight: FontWeight.w500,
              fontSize: 14,
              color: AppColors.background,
            ),
          ),
        ),
      );
    }

    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: _isExecuting ? null : _executeChain,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primaryBlue,
          disabledBackgroundColor: AppColors.primaryBlue,
          foregroundColor: AppColors.background,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        child: _isExecuting
            ? Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        AppColors.background,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'Executing...',
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.w500,
                      fontSize: 14,
                      color: AppColors.background,
                    ),
                  ),
                ],
              )
            : Text(
                'Run Plan →',
                style: GoogleFonts.poppins(
                  fontWeight: FontWeight.w500,
                  fontSize: 14,
                  color: AppColors.background,
                ),
              ),
      ),
    );
  }

  // ─── Helpers ──────────────────────────────────────────────
  String _formatNumber(int n) {
    // Pakistani-style formatting: 7,20,000
    final str = n.toString();
    if (str.length <= 3) return str;
    final last3 = str.substring(str.length - 3);
    final rest = str.substring(0, str.length - 3);
    final buffer = StringBuffer();
    for (int i = 0; i < rest.length; i++) {
      if (i > 0 && (rest.length - i) % 2 == 0) buffer.write(',');
      buffer.write(rest[i]);
    }
    return '$buffer,$last3';
  }
}

// ═════════════════════════════════════════════════════════════
// PRIVATE WIDGETS
// ═════════════════════════════════════════════════════════════

/// Small pill used in the budget summary card.
class _BudgetPill extends StatelessWidget {
  final String label;
  const _BudgetPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Text(
        label,
        style: GoogleFonts.poppins(
          fontSize: 11,
          fontWeight: FontWeight.w400,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
