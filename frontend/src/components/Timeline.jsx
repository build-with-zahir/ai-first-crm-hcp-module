import { CalendarDays, RadioTower } from "lucide-react";
import { useSelector } from "react-redux";

export default function Timeline() {
  const { interactions } = useSelector((state) => state.crm);

  return (
    <section className="work-panel timeline-panel">
      <div className="compact-heading">
        <div>
          <p className="eyebrow">Activity</p>
          <h2>Interaction timeline</h2>
        </div>
      </div>

      <div className="timeline-list">
        {interactions.length === 0 ? (
          <p className="muted">No interactions logged for this HCP yet.</p>
        ) : (
          interactions.map((interaction) => (
            <article className="timeline-item" key={interaction.id}>
              <div className="timeline-topline">
                <span>
                  <RadioTower size={15} />
                  {interaction.channel.replace("_", " ")}
                </span>
                <span>
                  <CalendarDays size={15} />
                  {formatDate(interaction.interaction_date)}
                </span>
              </div>
              <h3>{interaction.intent.replaceAll("_", " ")}</h3>
              <p>{interaction.summary}</p>
              <div className="tag-row">
                <span className={`sentiment ${interaction.sentiment}`}>{interaction.sentiment}</span>
                {interaction.products_discussed.map((product) => (
                  <span className="product-tag" key={`${interaction.id}-${product}`}>
                    {product}
                  </span>
                ))}
              </div>
              {interaction.edited_reason ? (
                <p className="edit-note">Edited: {interaction.edited_reason}</p>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
