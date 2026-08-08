import { useState } from "react";

import building42 from "../assets/maps/42.svg";
import cantineM1 from "../assets/maps/cantine.svg";
import cantine0 from "../assets/maps/cantine.svg";
import f0 from "../assets/maps/f0.svg";
import f1 from "../assets/maps/f1.svg";
import f2 from "../assets/maps/f2.svg";
import f6 from "../assets/maps/f6.svg";
import play from "../assets/maps/play.svg";
import roof from "../assets/maps/roof.svg";
import stairs from "../assets/maps/stairs.svg";
import cat from "../assets/maps/cat.svg";

import { lastSighting } from "../data/cat";
import { sightings } from "../data/sighting";

import GameMenu from "./GameMenu";

const zones: any = {
  entrance: {
    id: "entrance",
    name: "42 Entrance",
    floor: "Entrance",
    image: building42,
  },

  cantine_m1: {
    id: "cantine_m1",
    name: "CantiSkate",
    floor: "-1",
    image: cantineM1,
  },

  cantine_0: {
    id: "cantine_0",
    name: "Shokudo",
    floor: "0",
    image: cantine0,
  },

  cantine_1: {
    id: "cantine_1",
    name: "La Piscine",
    floor: "0",
    image: cantine0,
  },

  f0: {
    id: "f0",
    name: "F0",
    floor: "0",
    image: f0,
  },

  f1: {
    id: "f1",
    name: "F1",
    floor: "1",
    image: f1,
  },

  f1b: {
    id: "f1b",
    name: "F1b",
    floor: "2",
    image: f1,
  },

  f2: {
    id: "f2",
    name: "F2",
    floor: "2",
    image: f2,
  },

  f6: {
    id: "f6",
    name: "F6",
    floor: "6",
    image: f6,
  },

  playroom: {
    id: "playroom",
    name: "Cafe avant la fin du monde",
    floor: "2",
    image: play,
  },

  roof2: {
    id: "roof2",
    name: "Terrase (2)",
    floor: "2",
    image: roof,
  },

  roof3: {
    id: "roof3",
    name: "Terrase (3)",
    floor: "3",
    image: roof,
  },

  stairs: {
    id: "stairs",
    name: "Stairs",
    floor: "All",
    image: stairs,
  },
};

export default function CampusMap() {
  const [page, setPage] = useState("intro");

  const [selectedZone, setSelectedZone] = useState(lastSighting.zone);

  // Player points
  const [points, setPoints] = useState(120);

  // Guess state
  const [guessZone, setGuessZone] = useState("");
  const [guessMessage, setGuessMessage] = useState("");

  // Report state
  const [reportZone, setReportZone] = useState("");
  const [reportTime, setReportTime] = useState("");
  const [reportPhoto, setReportPhoto] = useState<File | null>(null);
  const [reportMessage, setReportMessage] = useState("");

  const currentZone = zones[selectedZone];

  // ---------------------------------------------------------
  // HEAT MAP
  // ---------------------------------------------------------

  const heat: any = {};

  sightings.forEach((s) => {
    heat[s.zone] = (heat[s.zone] || 0) + 1;
  });

  // ---------------------------------------------------------
  // GUESS
  // ---------------------------------------------------------

function handleGuess() {
  if (!guessZone) {
    setGuessMessage("🐱 Choose a location first!");
    return;
  }

  if (points < 1) {
    setGuessMessage("😿 You don't have enough points.");
    return;
  }

  // Spend 1 point
  setPoints((previous) => previous - 1);

  const correct = guessZone === lastSighting.zone;

  if (correct) {
    // Correct answer → +3 points
    setPoints((previous) => previous + 3);

    setGuessMessage(
      "🎉 Meeeow! You found me! I was hiding right there!  +3 points!"
    );
  } else {
    setGuessMessage(
      "😿 Meow… not here! Better luck next time!"
    );
  }

  // Show the result briefly, then reveal the map
  setTimeout(() => {
    setPage("map");
    setGuessMessage("");
    setGuessZone("");
  }, 1800);
}


  // ---------------------------------------------------------
  // REPORT
  // ---------------------------------------------------------

  function handleReport() {
    if (!reportZone) {
      setReportMessage("📍 Please choose where you saw Moulinette.");
      return;
    }

    if (!reportTime) {
      setReportMessage("⏰ Please choose when you saw Moulinette.");
      return;
    }

    // For now this only confirms the report locally.
    // Later this function should call your backend API.
    console.log("CAT REPORT", {
      zone: reportZone,
      time: reportTime,
      photo: reportPhoto,
    });

    setReportMessage(
      "🐱 Thank you! Your Moulinette sighting has been reported."
    );

    setReportZone("");
    setReportTime("");
    setReportPhoto(null);
  }

  // =========================================================
  // INTRO
  // =========================================================

  if (page === "intro") {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <main className="flex min-h-screen items-center justify-center px-6 py-12">
          <div className="w-full max-w-lg rounded-2xl border border-amber-400/40 bg-slate-900 p-8 text-center shadow-2xl">

            {/* MOULINETTE ONLY HERE */}

            <div className="mb-6 flex justify-center">
              <div className="relative flex h-40 w-40 items-center justify-center">
                <div className="cat-glow" />

                <img
                  src={cat}
                  alt="Moulinette"
                  className="cat-icon"
                />
              </div>
            </div>

            <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-amber-400">
              Moulinette
            </p>

            <h2 className="text-3xl font-bold">
              Meow! 🐱
            </h2>

            <p className="mt-4 text-lg text-slate-300">
              Do you want to guess where I am?
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Guessing costs 1 point. A correct answer gives you 3 points.
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">

              <button
                onClick={() => {
                  setGuessMessage("");
                  setGuessZone("");
                  setPage("guess");
                }}
                className="rounded-xl bg-amber-400 px-5 py-4 font-bold text-slate-950 hover:bg-amber-300"
              >
                🎯 Yes, let me guess!
              </button>

              <button
                onClick={() => setPage("map")}
                className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-4 font-semibold hover:bg-slate-700"
              >
                😿 No thanks, show me
              </button>

            </div>

          </div>
        </main>
      </div>
    );
  }

  // =========================================================
  // GUESS
  // =========================================================

  if (page === "guess") {
    return (
      <div className="min-h-screen bg-slate-950 px-6 py-8 text-white">

        <div className="mx-auto max-w-3xl">

          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-amber-400">
                🎯 Where is Moulinette?
              </h1>

              <p className="mt-2 text-slate-400">
                Choose the place where you think she is hiding.
              </p>
            </div>

            <div className="text-right">
              <p className="text-sm text-slate-400">
                Your points
              </p>

              <p className="text-xl font-bold text-amber-400">
                ⭐ {points}
              </p>
            </div>
          </div>

          {/* NO CAT IMAGE HERE */}

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

            <h2 className="mb-5 text-xl font-semibold">
              📍 Choose a location
            </h2>

            <div className="grid gap-3 sm:grid-cols-2">

              {Object.keys(zones).map((zone) => (
                <button
                  key={zone}
                  onClick={() => {
                    setGuessZone(zone);
                    setGuessMessage("");
                  }}
                  className={`rounded-xl border p-4 text-left transition ${
                    guessZone === zone
                      ? "border-amber-400 bg-amber-400/20"
                      : "border-slate-700 bg-slate-800 hover:border-amber-400"
                  }`}
                >
                  <span className="font-semibold">
                    {zones[zone].name}
                  </span>

                  <span className="mt-1 block text-sm text-slate-400">
                    Floor {zones[zone].floor}
                  </span>
                </button>
              ))}

            </div>

            <button
              onClick={handleGuess}
              disabled={!guessZone || points < 1}
              className="mt-6 w-full rounded-xl bg-amber-400 px-5 py-4 font-bold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              🎯 Confirm my guess — ⭐ 1 point
            </button>

            {guessMessage && (
              <div className="mt-5 rounded-xl border border-amber-400/40 bg-slate-800 p-4 text-center">
                {guessMessage}
              </div>
            )}

            <button
              onClick={() => setPage("map")}
              className="mt-4 w-full rounded-xl border border-slate-700 px-5 py-3 text-slate-300 hover:bg-slate-800"
            >
              Skip and see the map
            </button>

          </div>

        </div>

        <GameMenu
          page={page}
          setPage={setPage}
        />

      </div>
    );
  }

  // =========================================================
  // REPORT
  // =========================================================

  if (page === "report") {
    return (
      <div className="min-h-screen bg-slate-950 px-6 py-8 text-white">

        <div className="mx-auto max-w-2xl">

          <h1 className="text-3xl font-bold text-amber-400">
            ➕ Report Moulinette
          </h1>

          <p className="mt-2 text-slate-400">
            Saw Moulinette? Tell the campus cat community!
          </p>

          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">

            {/* ZONE */}

            <label className="block text-sm font-semibold text-slate-300">
              📍 Where did you see her?
            </label>

            <select
              value={reportZone}
              onChange={(e) => setReportZone(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-800 p-3 text-white"
            >
              <option value="">
                Select a location
              </option>

              {Object.keys(zones).map((zone) => (
                <option key={zone} value={zone}>
                  {zones[zone].name}
                </option>
              ))}
            </select>

            {/* TIME */}

            <label className="mt-6 block text-sm font-semibold text-slate-300">
              ⏰ When did you see her?
            </label>

            <input
              type="datetime-local"
              value={reportTime}
              onChange={(e) => setReportTime(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-800 p-3 text-white"
            />

            {/* PHOTO */}

            <label className="mt-6 block text-sm font-semibold text-slate-300">
              📷 Upload a photo
            </label>

            <input
              type="file"
              accept="image/*"
              onChange={(e) =>
                setReportPhoto(e.target.files?.[0] || null)
              }
              className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-800 p-3 text-sm"
            />

            {reportPhoto && (
              <p className="mt-2 text-sm text-slate-400">
                📎 {reportPhoto.name}
              </p>
            )}

            {/* SUBMIT */}

            <button
              onClick={handleReport}
              className="mt-8 w-full rounded-xl bg-amber-400 px-5 py-4 font-bold text-slate-950 hover:bg-amber-300"
            >
              🐱 Submit sighting
            </button>

            {reportMessage && (
              <div className="mt-5 rounded-xl border border-amber-400/40 bg-slate-800 p-4 text-center">
                {reportMessage}
              </div>
            )}

          </div>

        </div>

        <GameMenu
          page={page}
          setPage={setPage}
        />

      </div>
    );
  }

  // =========================================================
  // MAIN MAP
  // =========================================================

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 pb-32 text-white">

      {/* MAP */}

      {page === "map" && (
        <div>

          <h1 className="mb-6 text-3xl font-bold text-amber-400">
            🗺 Campus Map
          </h1>

          {/* ZONE SELECTOR */}

          <div className="mb-6 flex flex-wrap gap-3">

            {Object.keys(zones).map((zone) => (
              <button
                key={zone}
                onClick={() => setSelectedZone(zone)}
                className={`rounded-lg border px-3 py-2 ${
                  selectedZone === zone
                    ? "border-amber-400 bg-amber-400 text-slate-950"
                    : "border-yellow-400 bg-slate-800 hover:bg-yellow-600"
                }`}
              >
                {zones[zone].name}
              </button>
            ))}

          </div>

          {/* MAP IMAGE */}

          <div className="relative flex justify-center">

            <img
              src={currentZone.image}
              alt={currentZone.name}
              className="map-svg"
            />

            {selectedZone === lastSighting.zone && (
              <img
                src={cat}
                alt="Moulinette"
                className="cat-icon"
              />
            )}

          </div>

          {/* LAST SEEN */}

          <div className="mt-6 rounded-xl border border-yellow-400 bg-slate-900 p-5">

            <h2 className="text-xl text-yellow-400">
              📍 Last Seen
            </h2>

            <p className="mt-2">
              Zone: {lastSighting.zone}
            </p>

            <p>
              Reporter: {lastSighting.reporter}
            </p>

            <p>
              Time: {lastSighting.time}
            </p>

          </div>

        </div>
      )}

      {/* =====================================================
          HISTORY
      ===================================================== */}

      {page === "history" && (
        <div>

          <h1 className="mb-6 text-3xl font-bold text-amber-400">
            🐾 Cat History
          </h1>

          {sightings.map((s, index) => (
            <div
              key={index}
              className="mb-3 rounded-xl bg-slate-900 p-4"
            >
              🐾 {zones[s.zone]?.name || s.zone}

              <br />

              👤 {s.reporter}

              <br />

              ⏰ {s.time}
            </div>
          ))}

        </div>
      )}

      {/* =====================================================
          HEAT MAP
      ===================================================== */}

      {page === "heat" && (
        <div>

          <h1 className="mb-6 text-3xl font-bold text-amber-400">
            🔥 Cat Hotspots
          </h1>

          {Object.keys(heat).map((zone) => (
            <div
              key={zone}
              className="mb-3 rounded-xl bg-slate-900 p-4"
            >
              <p className="font-semibold">
                {zones[zone]?.name || zone}
              </p>

              <p className="mt-2">
                {"🐱".repeat(heat[zone])}
              </p>
            </div>
          ))}

        </div>
      )}

      {/* =====================================================
          DIARY
      ===================================================== */}

      {page === "diary" && (
        <div className="rounded-xl bg-slate-900 p-6">

          <h1 className="text-3xl font-bold text-amber-400">
            📖 Moulinette's Diary
          </h1>

          <p className="mt-6 text-slate-300">
            Today I explored the campus...
          </p>

          <p className="mt-2">
            Meow 🐱
          </p>

        </div>
      )}

      {/* =====================================================
          RANKING
      ===================================================== */}

      {page === "ranking" && (
        <div className="rounded-xl bg-slate-900 p-6">

          <h1 className="text-3xl font-bold text-amber-400">
            🏆 Ranking
          </h1>

          <div className="mt-6 space-y-3">

            <p>🥇 Test — 250 pts</p>
            <p>🥈 Test — 180 pts</p>
            <p>🥉 Test — 150 pts</p>

          </div>

        </div>
      )}

      <GameMenu
        page={page}
        setPage={setPage}
      />

    </div>
  );
}