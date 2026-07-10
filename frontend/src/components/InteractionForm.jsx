import { Mic, Plus, Save, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { createInteraction, selectHcp, updateLatestInteraction } from "../features/crmSlice.js";

const interactionTypes = [
  { label: "Meeting", value: "in_person" },
  { label: "Phone Call", value: "phone" },
  { label: "Email", value: "email" },
  { label: "Video Call", value: "video" },
  { label: "Conference", value: "conference" },
];

const defaultForm = {
  channel: "in_person",
  interactionDate: "2025-04-19",
  interactionTime: "19:36",
  attendees: "",
  topics:
    "Discussed CardioFlow efficacy, patient access barriers, positive sentiment, and requested a follow-up next week with outcomes data.",
  voiceSummary: false,
  materialSearch: "",
  materials: "",
  products_discussed: "CardioFlow",
  next_steps: "Send outcomes data; Schedule follow-up next week",
  edited_reason: "Corrected after field review.",
};

export default function InteractionForm() {
  const dispatch = useDispatch();
  const { selectedHcpId, hcps, interactions, saving } = useSelector((state) => state.crm);
  const selectedHcp = useMemo(
    () => hcps.find((hcp) => hcp.id === selectedHcpId),
    [hcps, selectedHcpId],
  );
  const [form, setForm] = useState(defaultForm);
  const [hcpName, setHcpName] = useState("");

  useEffect(() => {
    if (selectedHcp && hcpName !== selectedHcp.name) {
      setHcpName(selectedHcp.name);
    }
  }, [hcpName, selectedHcp]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function selectMatchingHcp(value) {
    setHcpName(value);
    const match = hcps.find((hcp) => hcp.name.toLowerCase() === value.toLowerCase());
    if (match) {
      dispatch(selectHcp(match.id));
    }
  }

  function submitInteraction(event) {
    event.preventDefault();
    dispatch(
      createInteraction({
        channel: form.channel,
        interaction_date: buildInteractionDate(form.interactionDate, form.interactionTime),
        raw_notes: buildNotes(form, selectedHcp),
        products_discussed: splitList(form.products_discussed),
        next_steps: splitList(form.next_steps),
      }),
    );
  }

  function editLatest() {
    dispatch(
      updateLatestInteraction({
        summary: form.topics,
        channel: form.channel,
        products_discussed: splitList(form.products_discussed),
        next_steps: splitList(form.next_steps),
        edited_reason: form.edited_reason,
      }),
    );
  }

  return (
    <form className="interaction-form" onSubmit={submitInteraction}>
      <div className="form-heading">
        <h1>Log HCP Interaction</h1>
      </div>

      <div className="section-label">Interaction Details</div>

      <div className="two-column">
        <label>
          HCP Name
          <input
            list="hcp-options"
            value={hcpName}
            onChange={(event) => selectMatchingHcp(event.target.value)}
            placeholder="Search or select HCP..."
          />
          <datalist id="hcp-options">
            {hcps.map((hcp) => (
              <option key={hcp.id} value={hcp.name}>
                {hcp.specialty} - {hcp.organization}
              </option>
            ))}
          </datalist>
        </label>

        <label>
          Interaction Type
          <select
            value={form.channel}
            onChange={(event) => updateField("channel", event.target.value)}
          >
            {interactionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="two-column">
        <label>
          Date
          <input
            type="date"
            value={form.interactionDate}
            onChange={(event) => updateField("interactionDate", event.target.value)}
          />
        </label>
        <label>
          Time
          <input
            type="time"
            value={form.interactionTime}
            onChange={(event) => updateField("interactionTime", event.target.value)}
          />
        </label>
      </div>

      <label>
        Attendees
        <input
          value={form.attendees}
          onChange={(event) => updateField("attendees", event.target.value)}
          placeholder="Enter names or search..."
        />
      </label>

      <label>
        Topics Discussed
        <textarea
          value={form.topics}
          onChange={(event) => updateField("topics", event.target.value)}
          rows={5}
          placeholder="Enter key discussion points..."
        />
      </label>

      <label className="check-row">
        <input
          type="checkbox"
          checked={form.voiceSummary}
          onChange={(event) => updateField("voiceSummary", event.target.checked)}
        />
        <span>
          <Mic size={13} />
          Summarize from Voice Note (Requires Consent)
        </span>
      </label>

      <div className="section-title-row">
        <span>Materials Shared / Samples Distributed</span>
      </div>
      <div className="material-search">
        <input
          value={form.materialSearch}
          onChange={(event) => updateField("materialSearch", event.target.value)}
          placeholder="Search material or sample..."
        />
        <button type="button" className="mini-button" onClick={() => updateField("materials", form.materialSearch)}>
          <Search size={13} />
          Search/Add
        </button>
      </div>

      <p className="empty-materials">{form.materials || "No materials added."}</p>

      <div className="two-column">
        <label>
          Products
          <input
            value={form.products_discussed}
            onChange={(event) => updateField("products_discussed", event.target.value)}
            placeholder="CardioFlow, GlucoTrack"
          />
        </label>
        <label>
          Next steps
          <input
            value={form.next_steps}
            onChange={(event) => updateField("next_steps", event.target.value)}
            placeholder="Send paper; schedule follow-up"
          />
        </label>
      </div>

      <label>
        Edit reason
        <input
          value={form.edited_reason}
          onChange={(event) => updateField("edited_reason", event.target.value)}
          placeholder="Why was the logged data changed?"
        />
      </label>

      <div className="button-row">
        <button className="primary-button" type="submit" disabled={!selectedHcpId || saving}>
          <Save size={17} />
          Log interaction
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!selectedHcpId || saving || interactions.length === 0}
          onClick={editLatest}
        >
          Edit latest
        </button>
      </div>
    </form>
  );
}

function buildNotes(form, selectedHcp) {
  const pieces = [
    selectedHcp ? `HCP: ${selectedHcp.name}` : "",
    form.attendees ? `Attendees: ${form.attendees}` : "",
    form.topics,
    form.materials ? `Materials or samples: ${form.materials}` : "",
    form.voiceSummary ? "Voice note consent captured for summarization." : "",
  ];
  return pieces.filter(Boolean).join(" ");
}

function buildInteractionDate(date, time) {
  if (!date || !time) {
    return undefined;
  }
  return new Date(`${date}T${time}:00`).toISOString();
}

function splitList(value) {
  return value
    .split(/[;,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}
