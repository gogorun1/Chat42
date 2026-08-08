import { useState } from "react";

interface ReportButtonProps {
  zones: Record<
    string,
    {
      id: string;
      name: string;
      floor: string;
    }
  >;
}

export default function ReportButton({
  zones,
}: ReportButtonProps) {
  const [open, setOpen] = useState(false);
  const [zone, setZone] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    console.log({
      zone,
      date,
      time,
    });

    // Later:
    // await api.post("/sightings", {
    //   zone,
    //   date,
    //   time,
    // });

    setSubmitted(true);
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-6 w-full rounded-xl border-2 border-yellow-400 bg-yellow-400 px-5 py-4 font-bold text-slate-950 shadow-[4px_4px_0px_#000] transition hover:bg-yellow-300"
      >
        📍 Report Moulinette
      </button>
    );
  }

  return (
    <div className="mt-6 rounded-2xl border-2 border-yellow-400 bg-slate-900 p-6">
      <h2 className="text-xl font-bold text-yellow-400">
        📍 Report a sighting
      </h2>

      {submitted ? (
        <div className="mt-5 text-center">
          <p className="text-lg text-green-400">
            🐾 Thank you!
          </p>

          <p className="mt-2 text-sm text-slate-400">
            Your Moulinette sighting has been recorded.
          </p>

          <button
            onClick={() => {
              setSubmitted(false);
              setOpen(false);
            }}
            className="mt-5 rounded-lg border border-slate-600 px-4 py-2 text-sm"
          >
            Close
          </button>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="mt-5 space-y-4"
        >
          {/* Zone */}
          <div>
            <label className="mb-1 block text-sm text-slate-400">
              Where did you see Moulinette?
            </label>

            <select
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-600 bg-slate-800 p-3 text-white"
            >
              <option value="">
                Select a zone
              </option>

              {Object.values(zones).map((item) => (
                <option
                  key={item.id}
                  value={item.id}
                >
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="mb-1 block text-sm text-slate-400">
              Date
            </label>

            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-600 bg-slate-800 p-3 text-white"
            />
          </div>

          {/* Time */}
          <div>
            <label className="mb-1 block text-sm text-slate-400">
              Time
            </label>

            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-600 bg-slate-800 p-3 text-white"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              className="flex-1 rounded-lg bg-yellow-400 px-4 py-3 font-bold text-slate-950 hover:bg-yellow-300"
            >
              📍 Submit
            </button>

            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg border border-slate-600 px-4 py-3"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}