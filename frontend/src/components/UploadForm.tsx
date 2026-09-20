import { useEffect, useState } from "react";
import type { QuestionnaireInput } from "../api/client";
import { captureOrPickPhoto, isNativeCameraAvailable } from "../capacitor/camera";
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
  const [isNative, setIsNative] = useState(false);
  const [captureError, setCaptureError] = useState<string | null>(null);

  useEffect(() => {
    isNativeCameraAvailable().then(setIsNative);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!image) return;
    onSubmit(image, questionnaire);
  };

  const handleNativeCapture = async () => {
    setCaptureError(null);
    try {
      const photo = await captureOrPickPhoto();
      if (photo) setImage(photo);
    } catch (err) {
      // A cancelled camera/gallery picker also lands here -- don't treat
      // that as an error worth showing the user, just leave the photo
      // field empty and let them try again.
      setCaptureError(
        err instanceof Error && !err.message.toLowerCase().includes("cancel")
          ? "Couldn't get a photo -- try again or use a different photo."
          : null,
      );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <div className="photo-upload">
        <span className="photo-upload-label">Photo of the rash</span>

        {isNative ? (
          <>
            <button type="button" className="capture-button" onClick={handleNativeCapture}>
              {image ? "Retake / Choose Different Photo" : "Take or Choose Photo"}
            </button>
            {image && <span className="hint">Selected: {image.name}</span>}
          </>
        ) : (
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
            required
          />
        )}

        {captureError && (
          <span className="hint" role="alert">
            {captureError}
          </span>
        )}

        <span className="hint">
          Center the rash in the frame with good lighting. This photo is the
          primary input — the questions below only add context.
        </span>
      </div>

      <Questionnaire value={questionnaire} onChange={setQuestionnaire} />

      <button type="submit" disabled={!image || submitting}>
        {submitting ? "Analyzing…" : "Get triage guidance"}
      </button>
    </form>
  );
}
