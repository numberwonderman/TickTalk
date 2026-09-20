export type TriageLevel =
  | "seek_care_urgent"
  | "seek_care_soon"
  | "seek_care_if_symptoms_change";

export interface OpenCvFeatures {
  border_irregularity: number;
  color_variance: number;
  radial_ring_score: number;
}

export interface TriageResponse {
  level: TriageLevel;
  headline: string;
  rationale: string;
  disclaimer: string;
  opencv_features: OpenCvFeatures;
  vision_confidence: number;
}

export interface QuestionnaireInput {
  tickExposure: boolean;
  rashDurationDays: number;
  fever: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function submitTriage(
  image: File,
  questionnaire: QuestionnaireInput,
): Promise<TriageResponse> {
  const form = new FormData();
  form.append("image", image);
  form.append("tick_exposure", String(questionnaire.tickExposure));
  form.append("rash_duration_days", String(questionnaire.rashDurationDays));
  form.append("fever", String(questionnaire.fever));

  const response = await fetch(`${API_BASE_URL}/api/triage`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Triage request failed (${response.status}): ${detail}`);
  }

  return (await response.json()) as TriageResponse;
}
