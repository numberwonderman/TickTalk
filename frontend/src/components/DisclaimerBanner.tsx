/**
 * Always visible, never dismissible. Rendered at the top of every screen
 * (see App.tsx) — this is a product requirement, not a styling choice.
 */
export function DisclaimerBanner() {
  return (
    <div role="alert" className="disclaimer-banner">
      <strong>Not medical advice. Not a diagnosis.</strong>{" "}
      TickCheck only helps you decide how urgently to see a doctor — it
      cannot confirm or rule out Lyme disease. When in doubt, see a doctor.
    </div>
  );
}
