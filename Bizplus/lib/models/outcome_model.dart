class OutcomeModel {
  final String detectedRegion;
  final int ordersPerDayBefore;
  final int revenueAtRiskPkr;
  final int ordersPerDayAfter;
  final int projectedReach;
  final int revenueRecoveredPkr;
  final int campaignCostPkr;
  final double roas;
  final double chainLatencyS;
  final String otherRegionsStatus;

  const OutcomeModel({
    required this.detectedRegion,
    required this.ordersPerDayBefore,
    required this.revenueAtRiskPkr,
    required this.ordersPerDayAfter,
    required this.projectedReach,
    required this.revenueRecoveredPkr,
    required this.campaignCostPkr,
    required this.roas,
    required this.chainLatencyS,
    required this.otherRegionsStatus,
  });
}

// DEMO DATA — remove when backend ready
const demoOutcome = OutcomeModel(
  detectedRegion: 'Lahore',
  ordersPerDayBefore: 142,
  revenueAtRiskPkr: 1400000,
  ordersPerDayAfter: 186,
  projectedReach: 5200,
  revenueRecoveredPkr: 990000,
  campaignCostPkr: 720000,
  roas: 2.8,
  chainLatencyS: 4.9,
  otherRegionsStatus: 'All 5 other regions unchanged',
);
