import 'dart:async';
import '../widgets/bottom_nav_bar.dart';
import 'dart:collection';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/agent_status_pill.dart';
import '../services/websocket_service.dart';

/// S6 — Live Trace Screen
/// Visualizes the real-time agentic reasoning pipeline for BizPulse.
/// Implements dual-mode with automatic fallback to demo simulation.
class LiveTraceScreen extends StatefulWidget {
  const LiveTraceScreen({super.key});

  @override
  State<LiveTraceScreen> createState() => _LiveTraceScreenState();
}

class _LiveTraceScreenState extends State<LiveTraceScreen>
    with TickerProviderStateMixin {
  // State variables
  final List<Map<String, dynamic>> _events = [];
  final Queue<Map<String, dynamic>> _eventQueue = Queue();
  final Map<String, String> _agentStates = {
    'Ingestion': 'pending',
    'Insight': 'pending',
    'ConflictResolver': 'pending',
    'ActionPlanner': 'pending',
    'Executor': 'pending',
  };

  bool _isDemo = false;
  bool _isComplete = false;
  bool _userScrolledUp = false;
  int _agentsDoneCount = 0;

  late final ScrollController _scrollController;
  WebSocketChannel? _channel;
  Timer? _demoTimer;
  Timer? _drainTimer;

  // Animation controller for pulsing "Active" state
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
    _scrollController.addListener(_onScroll);

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);

    // Start connection logic
    _initConnection();
  }

  void _onScroll() {
    if (_scrollController.hasClients) {
      final pos = _scrollController.position;
      // If user is near bottom, consider them not "scrolled up"
      if (pos.pixels >= pos.maxScrollExtent - 80) {
        _userScrolledUp = false;
      } else {
        _userScrolledUp = true;
      }
    }
  }

  void _initConnection() {
    // Get runId from arguments
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final runId =
          ModalRoute.of(context)?.settings.arguments as String? ?? 'DEMO_RUN';

      try {
        _channel = WebSocketService.connect(runId);
        _startDrainTimer();

        _channel!.stream.listen(
          (data) {
            if (!mounted) return;
            final event = jsonDecode(data as String);
            _eventQueue.add(event);
          },
          onError: (_) => _startDemoTicker(),
          onDone: () {
            if (_events.isEmpty && mounted) _startDemoTicker();
          },
        );

        // Fallback timeout: if no events after 3 seconds, start demo
        Future.delayed(const Duration(seconds: 3), () {
          if (_events.isEmpty && mounted && !_isDemo) {
            _startDemoTicker();
          }
        });
      } catch (e) {
        _startDemoTicker();
      }
    });
  }

  void _startDemoTicker() {
    if (_isDemo || !mounted) return;
    setState(() => _isDemo = true);

    int index = 0;
    _demoTimer = Timer.periodic(const Duration(milliseconds: 400), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (index >= demoTraceEvents.length) {
        timer.cancel();
        setState(() => _isComplete = true);
        return;
      }

      final ev = demoTraceEvents[index];
      _updateAgentStep(ev['agent'], ev['kind']);
      setState(() => _events.add(ev));
      _maybeAutoScroll();
      index++;
    });
  }

  void _startDrainTimer() {
    _drainTimer = Timer.periodic(const Duration(milliseconds: 400), (_) {
      if (!mounted) return;
      if (_eventQueue.isNotEmpty) {
        final ev = _eventQueue.removeFirst();
        _updateAgentStep(ev['agent'], ev['kind']);
        setState(() => _events.add(ev));
        _maybeAutoScroll();

        if (_eventQueue.isEmpty && WebSocketService.isLastEvent(ev)) {
          setState(() => _isComplete = true);
        }
      }
    });
  }

  void _updateAgentStep(String? agent, String? kind) {
    if (agent == null) return;

    // Mapping for Monitor to Executor step
    String targetAgent = agent == 'Monitor' ? 'Executor' : agent;

    if (!_agentStates.containsKey(targetAgent)) return;

    if (kind == 'completed') {
      if (_agentStates[targetAgent] != 'done') {
        _agentStates[targetAgent] = 'done';
        _agentsDoneCount++;
      }
    } else if (kind == 'started') {
      if (_agentStates[targetAgent] != 'done') {
        _agentStates[targetAgent] = 'active';
      }
    }
  }

  void _maybeAutoScroll() {
    if (!_userScrolledUp && _scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _demoTimer?.cancel();
    _drainTimer?.cancel();
    _scrollController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.primaryBlue),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Live Trace',
          style: GoogleFonts.poppins(
            fontWeight: FontWeight.w500,
            fontSize: 18,
            color: AppColors.primaryDark,
          ),
        ),
        actions: [_buildBadge(), const SizedBox(width: 16)],
      ),
      body: Column(
        children: [
          _buildPipelineCard(),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(12),
              itemCount: _events.length + (_isComplete ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _events.length) {
                  return _buildOutcomeButton();
                }
                return _buildEventItem(_events[index], index);
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 1),
    );
  }

  Widget _buildBadge() {
    if (_isDemo) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          'DEMO',
          style: GoogleFonts.poppins(
            fontSize: 10,
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w600,
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF0EE),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _BlinkingDot(),
          const SizedBox(width: 4),
          Text(
            'LIVE',
            style: GoogleFonts.poppins(
              fontSize: 10,
              color: AppColors.error,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPipelineCard() {
    final agents = [
      'Ingestion',
      'Insight',
      'ConflictResolver',
      'ActionPlanner',
      'Executor',
    ];

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.background,
        border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(agents.length, (index) {
              final agent = agents[index];
              final state = _agentStates[agent] ?? 'pending';
              final isLast = index == agents.length - 1;

              return Expanded(
                child: Row(
                  children: [
                    Column(
                      children: [
                        Text(
                          agent == 'ConflictResolver' ? 'Conflict' : agent,
                          style: GoogleFonts.poppins(
                            fontSize: 9,
                            color: AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        _buildStepDot(state),
                      ],
                    ),
                    if (!isLast)
                      Expanded(
                        child: Container(
                          height: 1.5,
                          margin: const EdgeInsets.only(top: 14),
                          color: state == 'done'
                              ? AppColors.success
                              : AppColors.border,
                        ),
                      ),
                  ],
                ),
              );
            }),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              '$_agentsDoneCount of 5 agents complete',
              style: GoogleFonts.poppins(
                fontSize: 10,
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepDot(String state) {
    if (state == 'done') {
      return Container(
        width: 10,
        height: 10,
        decoration: const BoxDecoration(
          color: AppColors.success,
          shape: BoxShape.circle,
        ),
      );
    } else if (state == 'active') {
      return AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          return Opacity(
            opacity: 0.3 + (_pulseController.value * 0.7),
            child: Container(
              width: 10,
              height: 10,
              decoration: const BoxDecoration(
                color: AppColors.primaryBlue,
                shape: BoxShape.circle,
              ),
            ),
          );
        },
      );
    } else {
      return Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          border: Border.all(color: AppColors.border, width: 1.5),
        ),
      );
    }
  }

  Widget _buildEventItem(Map<String, dynamic> event, int index) {
    final level = event['level'] ?? 'info';
    Color leftBorder;
    switch (level) {
      case 'success':
        leftBorder = AppColors.success;
        break;
      case 'warn':
        leftBorder = AppColors.warning;
        break;
      case 'error':
        leftBorder = AppColors.error;
        break;
      default:
        leftBorder = AppColors.primaryBlue;
    }

    return TweenAnimationBuilder<double>(
      duration: const Duration(milliseconds: 300),
      tween: Tween(begin: 0.0, end: 1.0),
      curve: Curves.easeOut,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 20 * (1 - value)),
            child: child,
          ),
        );
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border, width: 0.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Level indicator (left border replacement with visual)
            Container(
              width: 3,
              height: 40,
              decoration: BoxDecoration(
                color: leftBorder,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 8),
            // Timestamp and Pill
            SizedBox(
              width: 52,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    event['ts'] ?? '--:--:--',
                    style: GoogleFonts.robotoMono(
                      fontSize: 9,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: AgentStatusPill.agent(event['agent'] ?? ''),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Message
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    event['message'] ?? '',
                    style: GoogleFonts.poppins(
                      fontSize: 11,
                      color: AppColors.textPrimary,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 4),
                  AgentStatusPill.kind(event['kind'] ?? ''),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOutcomeButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: InkWell(
        onTap: () {
          final runId = ModalRoute.of(context)?.settings.arguments as String?;
          Navigator.pushNamed(context, RouteNames.outcome, arguments: runId);
        },
        child: Container(
          height: 46,
          decoration: BoxDecoration(
            color: AppColors.success,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.bar_chart, color: Colors.white, size: 18),
              const SizedBox(width: 8),
              Text(
                'View Outcome →',
                style: GoogleFonts.poppins(
                  color: Colors.white,
                  fontWeight: FontWeight.w500,
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BlinkingDot extends StatefulWidget {
  @override
  _BlinkingDotState createState() => _BlinkingDotState();
}

class _BlinkingDotState extends State<_BlinkingDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 6,
        height: 6,
        decoration: const BoxDecoration(
          color: AppColors.error,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

// DEMO DATA — remove when backend ready
final demoTraceEvents = [
  {
    'ts': '10:42:01',
    'agent': 'Ingestion',
    'kind': 'completed',
    'level': 'success',
    'message': '6 sources ingested. 2 down-ranked (spam/low credibility).',
  },
  {
    'ts': '10:42:04',
    'agent': 'Insight',
    'kind': 'completed',
    'level': 'success',
    'message': '4 insights extracted. Outlier: Lahore −25%.',
  },
  {
    'ts': '10:42:07',
    'agent': 'ConflictResolver',
    'kind': 'completed',
    'level': 'success',
    'message': '2 contradictions resolved. 1 flagged: needs human review.',
  },
  {
    'ts': '10:42:10',
    'agent': 'ActionPlanner',
    'kind': 'completed',
    'level': 'success',
    'message': '5-action chain planned. Budget: 720k / 800k PKR.',
  },
  {
    'ts': '10:42:12',
    'agent': 'Executor',
    'kind': 'started',
    'level': 'info',
    'message': 'Running action chain...',
  },
  {
    'ts': '10:42:13',
    'agent': 'Executor',
    'kind': 'completed',
    'level': 'success',
    'message': 'A1 — Diagnose: 412 SKUs identified.',
  },
  {
    'ts': '10:42:14',
    'agent': 'Executor',
    'kind': 'completed',
    'level': 'success',
    'message': 'A2 — Managers notified via email.',
  },
  {
    'ts': '10:42:15',
    'agent': 'Executor',
    'kind': 'completed',
    'level': 'success',
    'message': 'A3 — Campaign launched in Lahore.',
  },
  {
    'ts': '10:42:20',
    'agent': 'Executor',
    'kind': 'failed',
    'level': 'error',
    'message': 'A4 — Notification API failed mid-send.',
  },
  {
    'ts': '10:42:21',
    'agent': 'Executor',
    'kind': 'retry',
    'level': 'warn',
    'message': 'A4 — Retrying with smaller batches...',
  },
  {
    'ts': '10:42:23',
    'agent': 'Executor',
    'kind': 'fallback',
    'level': 'warn',
    'message': 'A4 — Fallback: in-app banner draft created.',
  },
  {
    'ts': '10:42:24',
    'agent': 'Executor',
    'kind': 'completed',
    'level': 'success',
    'message': 'A4 — Pricing updated. Notifications drafted.',
  },
  {
    'ts': '10:42:25',
    'agent': 'Executor',
    'kind': 'completed',
    'level': 'success',
    'message': 'A5 — 7-day monitor scheduled. Auto-pause at ROAS < 1.5.',
  },
  {
    'ts': '10:42:25',
    'agent': 'Monitor',
    'kind': 'started',
    'level': 'info',
    'message': 'Watching all 6 regions. ROAS threshold active.',
  },
];
