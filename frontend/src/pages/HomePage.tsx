import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api, LeaderboardEntry } from "../lib/api";
import CampusMap from "../components/42map";

export function HomePage() {
  const { user, logout } = useAuth();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[] | null>(null);

  function loadLeaderboard() {
    api
      .get<LeaderboardEntry[]>("/gamification/leaderboard?limit=100")
      .then(setLeaderboard)
      .catch(() => undefined);
  }

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const myRank = leaderboard?.findIndex((entry) => entry.user_id === user?.id) ?? -1;
  const myEntry = myRank >= 0 ? leaderboard![myRank] : null;

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-8 text-white">
      <div className="mb-8 flex flex-col gap-4 rounded-xl border border-yellow-400 bg-slate-900 p-5 shadow-lg md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-yellow-400">🐱 Chat42</h1>
          <p className="mt-1 text-sm text-slate-400">Campus Cat Adventure</p>
        </div>

        <div className="flex items-center gap-5">
          <div className="text-right">
            <p className="text-sm text-slate-400">👤 {user?.email}</p>
            <p className="mt-1 font-bold text-yellow-400">⭐ {myEntry ? myEntry.score : "—"} pts</p>
            <p className="text-sm text-slate-400">🏆 {myRank >= 0 ? `Rank #${myRank + 1}` : "Unranked"}</p>
          </div>

          <button
            onClick={logout}
            className="rounded-md border border-slate-700 px-4 py-2 text-sm transition hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </div>

      {/*
        CampusMap owns its own upload/guess/diary flows internally, but the
        leaderboard is lifted up here so both the header's "my rank" card
        and CampusMap's Ranking tab read from the same fetch -- avoids two
        independent /gamification/leaderboard calls drifting out of sync.
      */}
      <CampusMap leaderboard={leaderboard} loadLeaderboard={loadLeaderboard} />
    </div>
  );
}