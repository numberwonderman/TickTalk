import type { TriageResponse } from "../api/client";

const LEVEL_CLASS: Record<TriageResponse["level"], string> = {
  seek_care_urgent: "level-urgent",
  seek_care_soon: "level-soon",
  seek_care_if_symptoms_change: "level-watch",
};

export function TriageResult({ result }: { result: TriageResponse }) {
  return (
    <div className={`triage-result ${LEVEL_CLASS[result.level]}`}>
      <h2>{result.headline}</h2>
      <p>{result.rationale}</p>
      <p className="disclaimer-inline">{result.disclaimer}</p>
    </div>
  );
}
