import { useState } from "react";
import { submitTriage, type QuestionnaireInput, type TriageResponse } from "./api/client";
import { DisclaimerBanner } from "./components/DisclaimerBanner";
import { TriageResult } from "./components/TriageResult";
import { UploadForm } from "./components/UploadForm";

export function App() {
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (image: File, questionnaire: QuestionnaireInput) => {
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitTriage(image, questionnaire);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app">
      <DisclaimerBanner />
      <header>
        <h1>TickCheck</h1>
        <p>A photo-first triage helper for possible tick-bite rashes.</p>
      </header>

      <UploadForm onSubmit={handleSubmit} submitting={submitting} />

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      {result && <TriageResult result={result} />}

      <DisclaimerBanner />
    </div>
  );
}
