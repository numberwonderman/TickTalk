import type { QuestionnaireInput } from "../api/client";

interface Props {
  value: QuestionnaireInput;
  onChange: (value: QuestionnaireInput) => void;
}

/**
 * Supplementary context only — the photo is the primary input. Copy here
 * should never imply these answers alone determine the result.
 */
export function Questionnaire({ value, onChange }: Props) {
  return (
    <fieldset className="questionnaire">
      <legend>A few supplementary details</legend>

      <label>
        <input
          type="checkbox"
          checked={value.tickExposure}
          onChange={(e) => onChange({ ...value, tickExposure: e.target.checked })}
        />
        I know or suspect I was bitten by a tick
      </label>

      <label>
        How many days has the rash been there?
        <input
          type="number"
          min={0}
          value={value.rashDurationDays}
          onChange={(e) =>
            onChange({ ...value, rashDurationDays: Number(e.target.value) })
          }
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={value.fever}
          onChange={(e) => onChange({ ...value, fever: e.target.checked })}
        />
        I currently have a fever
      </label>
    </fieldset>
  );
}
