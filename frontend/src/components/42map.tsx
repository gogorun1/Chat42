import { useEffect, useState } from "react";

import {
  api,
  ApiError,
  Diary,
  GuessResult,
  LeaderboardEntry,
  SearchSighting,
  SightingSearchResult,
  Zone,
} from "../lib/api";
import { useAuth } from "../context/AuthContext";

import building42 from "../assets/maps/building.svg";
import cantineM1 from "../assets/maps/cantine_m1.svg";
import cantine0 from "../assets/maps/cantine_0.svg";
import cantine1 from "../assets/maps/cantine_1.svg";
import f0 from "../assets/maps/f0.svg";
import f1 from "../assets/maps/f1.svg";
import f1b from "../assets/maps/f1b.svg";
import f2 from "../assets/maps/f2.svg";
import f6 from "../assets/maps/f6.svg";
import play from "../assets/maps/playroom.svg";
import roof2 from "../assets/maps/terrase_2.svg";
import roof3 from "../assets/maps/terrase_3.svg";
import stairs from "../assets/maps/stairs.svg";
import cat from "../assets/maps/cat.svg";

import { lastSighting } from "../data/cat";

import GameMenu from "./GameMenu";

export const zones: any = {
  entrance: { id: "entrance", name: "42 Entrance", floor: "Entrance", image: building42 },
  cantine_m1: { id: "cantine_m1", name: "CantiSkate", floor: "-1", image: cantineM1 },
  cantine_0: { id: "cantine_0", name: "Shokudo", floor: "0", image: cantine0 },
  cantine_1: { id: "cantine_1", name: "La Piscine", floor: "0", image: cantine1 },
  f0: { id: "f0", name: "F0", floor: "0", image: f0 },
  f1: { id: "f1", name: "F1", floor: "1", image: f1 },
  f1b: { id: "f1b", name: "F1b", floor: "2", image: f1b },
  f2: { id: "f2", name: "F2", floor: "2", image: f2 },
  f6: { id: "f6", name: "F6", floor: "6", image: f6 },
  playroom: { id: "playroom", name: "Cafe avant la fin du monde", floor: "2", image: play },
  roof2: { id: "roof2", name: "Terrase(2)", floor: "2", image: roof2 },
  roof3: { id: "roof3", name: "Terrase(3)", floor: "3", image: roof3 },
  stairs: { id: "stairs", name: "Stairs", floor: "All", image: stairs },
};

type CampusMapProps = {
  leaderboard: LeaderboardEntry[] | null;
  loadLeaderboard: () => void;
};

export default function CampusMap({ leaderboard, loadLeaderboard }: CampusMapProps) {
  const { user, refreshUser } = useAuth();
  const [page, setPage] = useState("intro");

  const [selectedZone, setSelectedZone] = useState(lastSighting.zone);

  // Player points — persisted server-side on the user (see
  // POST /gamification/guess), not local state, so it survives a refresh
  // and feeds into /gamification/leaderboard's score.
  const points = user?.guess_points ?? 0;

  // Guess state
  const [guessZone, setGuessZone] = useState("");
  const [guessMessage, setGuessMessage] = useState("");
  const [guessSubmitting, setGuessSubmitting] = useState(false);

  // Report state
  const [reportZone, setReportZone] = useState("");
  const [reportPhoto, setReportPhoto] = useState<File | null>(null);
  const [reportMessage, setReportMessage] = useState("");
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [backendZones, setBackendZones] = useState<Zone[]>([]);
  const [campusSightings, setCampusSightings] = useState<SearchSighting[]>([]);
  const [diary, setDiary] = useState<Diary | null>(null);
  const [diaryError, setDiaryError] = useState<string | null>(null);

  function loadCampusSightings() {
    // FIX: was missing the /api prefix -- confirmed via backend logs that
    // the real route is /api/search/sightings, not /search/sightings.
    // Every other call in this file (zones, ai/diary, sightings/,
    // gamification/guess) is correctly unprefixed per those same logs;
    // search is the one endpoint that's mounted under /api.
    api
      .get<SightingSearchResult>("/api/search/sightings?page_size=100&sort_by=created_at&sort_order=desc")
      .then((result) => setCampusSightings(result.items))
      .catch(() => undefined);
  }

  useEffect(() => {
    api
      .get<Zone[]>("/sightings/zones")
      .then(setBackendZones)
      .catch(() => undefined);
    loadCampusSightings();
    api
      .get<Diary>("/ai/diary")
      .then(setDiary)
      .catch((err) => setDiaryError(err instanceof ApiError ? err.message : "Failed to load diary"));
  }, []);

  const currentZone = zones[selectedZone];

  // Real "last seen" — most recent real sighting, mapped back to the local
  // zone/reporter/time shape the Guess flow and Last Seen card already use.
  // Falls back to the mock lastSighting until a real sighting exists.
  const mostRecentReal = campusSightings[0];
  const latestSighting = mostRecentReal
    ? {
        zone: backendZones.find((zone) => zone.id === mostRecentReal.zone_id)?.slug ?? lastSighting.zone,
        reporter: mostRecentReal.reporter,
        time: new Date(mostRecentReal.created_at).toLocaleTimeString(),
      }
    : lastSighting;

  // ---------------------------------------------------------
  // HEAT MAP
  // ---------------------------------------------------------

  const heat: any = {};

  campusSightings.forEach((s) => {
    const slug = backendZones.find((zone) => zone.id === s.zone_id)?.slug;
    if (slug) heat[slug] = (heat[slug] || 0) + 1;
  });

  // ---------------------------------------------------------
  // GUESS
  // ---------------------------------------------------------

  async function handleGuess() {
    if (!guessZone) {
      setGuessMessage("🐱 Choose a location first!");
      return;
    }

    if (points < 1) {
      setGuessMessage("😿 You don't have enough points.");
      return;
    }

    const backendZone = backendZones.find((zone) => zone.slug === guessZone);
    if (!backendZone) {
      setGuessMessage("😿 That location isn't set up on the server yet.");
      return;
    }

    setGuessSubmitting(true);

    try {
      const result = await api.post<GuessResult>("/gamification/guess", { zone_id: backendZone.id });
      await refreshUser();
      loadLeaderboard();

      setGuessMessage(
        result.correct
          ? "🎉 Meeeow! You found me! I was hiding right there!  +3 points!"
          : "😿 Meow… not here! Better luck next time!"
      );
    } catch (err) {
      setGuessMessage(err instanceof ApiError ? `😿 ${err.message}` : "😿 Failed to submit your guess.");
      setGuessSubmitting(false);
      return;
    }

    setGuessSubmitting(false);

    // Show the result briefly, then reveal the map open to where the cat
    // actually was
    setTimeout(() => {
      setSelectedZone(latestSighting.zone);
      setPage("map");
      setGuessMessage("");
      setGuessZone("");
    }, 1800);
  }

  // ---------------------------------------------------------
  // REPORT
  // ---------------------------------------------------------

  async function handleReport() {
    if (!reportZone) {
      setReportMessage("📍 Please choose where you saw Moulinette.");
      return;
    }

    if (!reportPhoto) {
      setReportMessage("📷 Please attach a photo.");
      return;
    }

    const backendZone = backendZones.find((zone) => zone.slug === reportZone);
    if (!backendZone) {
      setReportMessage("😿 That location isn't set up on the server yet.");
      return;
    }

    setReportSubmitting(true);
    setReportMessage("");

    const formData = new FormData();
    formData.append("zone_id", String(backendZone.id));
    formData.append("image", reportPhoto);

    try {
      await api.postForm("/sightings/", formData);
      setReportMessage("🐱 Thank you! Your Moulinette sighting has been reported.");
      await refreshUser();
      loadCampusSightings();
      loadLeaderboard();
      setReportZone("");
      setReportPhoto(null);
    } catch (err) {
      setReportMessage(err instanceof ApiError ? `😿 ${err.message}` : "😿 Failed to report sighting.");
    } finally {
      setReportSubmitting(false);
    }
  }

  // =========================================================
  // INTRO
  // =========================================================

  if (page === "intro") {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <main className="flex min-h-screen items-center justify-center px-6 py-12">
          <div className="w-full max-w-lg rounded-2xl border border-amber-400/40 bg-slate-900 p-8 text-center shadow-2xl">
            <div className="mb-6 flex justify-center">
              <div className="relative flex h-40 w-40 items-center justify-center">
                <div className="cat-glow" />
                <img src={cat} alt="Moulinette" className="cat-icon" />
              </div>
            </div>

            <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-amber-400">Moulinette</p>
            <h2 className="text-3xl font-bold">Meow! 🐱</h2>
            <p className="mt-4 text-lg text-slate-300">Do you want to guess where I am?</p>
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
                onClick={() => {
                  setSelectedZone(latestSighting.zone);
                  setPage("map");
                }}
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
              <h1 className="text-3xl font-bold text-amber-400">🎯 Where is Moulinette?</h1>
              <p className="mt-2 text-slate-400">Choose the place where you think she is hiding.</p>
            </div>

            <div className="text-right">
              <p className="text-sm text-slate-400">Your points</p>
              <p className="text-xl font-bold text-amber-400">⭐ {points}</p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-5 text-xl font-semibold">📍 Choose a location</h2>

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
                  <span className="font-semibold">{zones[zone].name}</span>
                  <span className="mt-1 block text-sm text-slate-400">Floor {zones[zone].floor}</span>
                </button>
              ))}
            </div>

            <button
              onClick={handleGuess}
              disabled={!guessZone || points < 1 || guessSubmitting}
              className="mt-6 w-full rounded-xl bg-amber-400 px-5 py-4 font-bold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {guessSubmitting ? "Confirming…" : "🎯 Confirm my guess — ⭐ 1 point"}
            </button>

            {guessMessage && (
              <div className="mt-5 rounded-xl border border-amber-400/40 bg-slate-800 p-4 text-center">
                {guessMessage}
              </div>
            )}

            <button
              onClick={() => {
                setSelectedZone(latestSighting.zone);
                setPage("map");
              }}
              className="mt-4 w-full rounded-xl border border-slate-700 px-5 py-3 text-slate-300 hover:bg-slate-800"
            >
              Skip and see the map
            </button>
          </div>
        </div>

        <GameMenu page={page} setPage={setPage} />
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
          <h1 className="text-3xl font-bold text-amber-400">➕ Report Moulinette</h1>
          <p className="mt-2 text-slate-400">Saw Moulinette? Tell the campus cat community!</p>

          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <label className="block text-sm font-semibold text-slate-300">📍 Where did you see her?</label>
            <select
              value={reportZone}
              onChange={(e) => setReportZone(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-800 p-3 text-white"
            >
              <option value="">Select a location</option>
              {Object.keys(zones).map((zone) => (
                <option key={zone} value={zone}>
                  {zones[zone].name}
                </option>
              ))}
            </select>

            <label className="mt-6 block text-sm font-semibold text-slate-300">📷 Upload a photo</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setReportPhoto(e.target.files?.[0] || null)}
              className="mt-2 block w-full rounded-xl border border-slate-700 bg-slate-800 p-3 text-sm"
            />

            {reportPhoto && <p className="mt-2 text-sm text-slate-400">📎 {reportPhoto.name}</p>}

            <button
              onClick={handleReport}
              disabled={reportSubmitting}
              className="mt-8 w-full rounded-xl bg-amber-400 px-5 py-4 font-bold text-slate-950 hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {reportSubmitting ? "Submitting…" : "🐱 Submit sighting"}
            </button>

            {reportMessage && (
              <div className="mt-5 rounded-xl border border-amber-400/40 bg-slate-800 p-4 text-center">
                {reportMessage}
              </div>
            )}
          </div>
        </div>

        <GameMenu page={page} setPage={setPage} />
      </div>
    );
  }

  // =========================================================
  // MAIN MAP
  // =========================================================

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 pb-32 text-white">
      {page === "map" && (
        <div>
          <h1 className="mb-6 text-3xl font-bold text-amber-400">🗺 Campus Map</h1>

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

          <div className="relative flex justify-center">
            <img src={currentZone.image} alt={currentZone.name} className="map-svg" />
            {selectedZone === latestSighting.zone && (
              <img src={cat} alt="Moulinette" className="cat-icon cat-icon-map" />
            )}
          </div>

          <div className="mt-6 rounded-xl border border-yellow-400 bg-slate-900 p-5">
            <h2 className="text-xl text-yellow-400">📍 Last Seen</h2>
            <p className="mt-2">Zone: {latestSighting.zone}</p>
            <p>Reporter: {latestSighting.reporter}</p>
            <p>Time: {latestSighting.time}</p>
          </div>
        </div>
      )}

      {page === "history" && (
        <div>
          <h1 className="mb-6 text-3xl font-bold text-amber-400">🐾 Cat History</h1>

          {campusSightings.map((s) => (
            <div key={s.id} className="mb-3 rounded-xl bg-slate-900 p-4">
              🐾 {s.zone_name}
              <br />
              👤 {s.reporter}
              <br />
              ⏰ {new Date(s.created_at).toLocaleString()}
            </div>
          ))}

          {campusSightings.length === 0 && <p className="text-slate-500">No sightings reported yet.</p>}
        </div>
      )}

      {page === "heat" && (
        <div>
          <h1 className="mb-6 text-3xl font-bold text-amber-400">🔥 Cat Hotspots</h1>

          {Object.keys(heat).map((zone) => (
            <div key={zone} className="mb-3 rounded-xl bg-slate-900 p-4">
              <p className="font-semibold">{zones[zone]?.name || zone}</p>
              <p className="mt-2">{"🐱".repeat(heat[zone])}</p>
            </div>
          ))}
        </div>
      )}

      {page === "diary" && (
        <div className="rounded-xl bg-slate-900 p-6">
          <h1 className="text-3xl font-bold text-amber-400">📖 Moulinette's Diary</h1>

          {diary && <p className="mt-2 text-sm text-slate-500">{diary.date}</p>}
          {diaryError && <p className="mt-6 text-red-400">😿 {diaryError}</p>}
          {!diary && !diaryError && <p className="mt-6 text-slate-400">Moulinette is writing today's entry…</p>}
          {diary && <p className="mt-6 whitespace-pre-line text-slate-300">{diary.content}</p>}
        </div>
      )}

      {page === "ranking" && (
        <div className="rounded-xl bg-slate-900 p-6">
          <h1 className="text-3xl font-bold text-amber-400">🏆 Ranking</h1>

          <div className="mt-6 space-y-3">
            {leaderboard?.map((entry, index) => {
              const medal = ["🥇", "🥈", "🥉"][index] ?? `#${index + 1}`;
              const isMe = entry.user_id === user?.id;
              return (
                <p key={entry.user_id} className={isMe ? "font-bold text-amber-300" : ""}>
                  {medal} {entry.display_name ?? `User #${entry.user_id}`} — {entry.score} pts
                </p>
              );
            })}

            {leaderboard && leaderboard.length === 0 && <p className="text-slate-500">No one on the board yet.</p>}
          </div>
        </div>
      )}

      <GameMenu page={page} setPage={setPage} />
    </div>
  );
}