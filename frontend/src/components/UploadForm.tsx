import { useState } from "react";
import type { QuestionnaireInput } from "../api/client";
import { Questionnaire } from "./Questionnaire";

interface Props {
  onSubmit: (image: File, questionnaire: QuestionnaireInput) => void;
  submitting: boolean;
}

const DEFAULT_QUESTIONNAIRE: QuestionnaireInput = {
  tickExposure: false,
  rashDurationDays: 0,
  fever: false,
};

export function UploadForm({ onSubmit, submitting }: Props) {
  const [image, setImage] = useState<File | null>(null);
  const [questionnaire, setQuestionnaire] = useState(DEFAULT_QUESTIONNAIRE);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!image) return;
    onSubmit(image, questionnaire);
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <label className="photo-upload">
        Photo of the rash
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          required
        />
        <span className="hint">
          Center the rash in the frame with good lighting. This photo is the
          primary input — the questions below only add context.
        </span>
      </label>

      <Questionnaire value={questionnaire} onChange={setQuestionnaire} />

      <button type="submit" disabled={!image || submitting}>
        {submitting ? "Analyzing…" : "Get triage guidance"}
      </button>
    </form>
  );
}
