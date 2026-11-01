export const SUBTYPE_LABELS: Record<string, string> = {
  // percentages
  percent_of_number: "Percent of a number",
  what_percent: "What percent",
  percent_change: "Percentage change",
  successive_change: "Successive changes",
  find_original: "Find the original number",
  discount_price: "Discount and selling price",
  // ratios
  ratio_share: "Sharing in a ratio",
  ratio_missing_term: "Missing term of a ratio",
  proportion: "Direct proportion",
  ratio_difference: "Ratio with a difference",
  ratio_chain: "Linked ratios (A:B, B:C)",
  // profit and loss
  pl_profit_percent: "Profit percent",
  pl_loss_percent: "Loss percent",
  pl_selling_price: "Selling price from profit",
  pl_cost_price: "Cost price from loss",
  pl_markup_discount: "Markup then discount",
  pl_two_articles: "Two articles, equal gain and loss",
  // time and work
  tw_together: "Working together",
  tw_alone: "One worker's time alone",
  tw_leaving: "A worker leaves midway",
  tw_wages: "Sharing wages",
  tw_pipes: "Pipes and tanks",
  // averages and mixtures
  avg_new_member: "Average with a new member",
  avg_replace: "Replacing a number in an average",
  avg_combined: "Combined average",
  avg_speed: "Average speed",
  mix_quantity: "Mixing at different prices",
  mix_replace: "Replacing part of a mixture",
  // interest
  int_si: "Simple interest",
  int_si_rate: "Rate of simple interest",
  int_si_time: "Time for simple interest",
  int_ci_amount: "Compound amount",
  int_ci_diff: "Compound vs simple interest difference",
  int_si_multiple: "Time to multiply money (simple interest)",
};

/** Friendly name for a question type; also works for plain keys like "easy". */
export function subtypeLabel(key: string): string {
  return SUBTYPE_LABELS[key] ?? key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
}