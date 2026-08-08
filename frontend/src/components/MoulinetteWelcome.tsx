import cat from "../assets/maps/cat.svg";

interface MoulinetteWelcomeProps {
  points: number;
  onGuess: () => void;
  onSkip: () => void;
}

export default function MoulinetteWelcome({
  points,
  onGuess,
  onSkip,
}: MoulinetteWelcomeProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 pb-10 text-white">
      <div className="w-full max-w-md rounded-2xl border-4 border-yellow-400 bg-slate-900 p-8 text-center shadow-[8px_8px_0px_#000]">

        {/* Player points */}
        <div className="mb-4 text-right text-sm font-bold text-yellow-300">
          ⭐ {points} pts
        </div>

        {/* Moulinette */}
        <div className="relative mx-auto mb-6 flex h-52 items-center justify-center">
          <div className="absolute h-40 w-40 animate-pulse rounded-full bg-yellow-400/20 blur-xl" />

          <img
            src={cat}
            alt="Moulinette"
            className="relative z-10 w-40 image-rendering-pixelated drop-shadow-[0_0_15px_#facc15]"
          />
        </div>

        {/* Speech bubble */}
        <div className="relative mb-8 rounded-2xl border-2 border-yellow-400 bg-slate-800 p-5">
          <p className="text-xl font-bold text-yellow-300">
            🐱 Miaou!
          </p>

          <p className="mt-2 text-lg">
            Do you want to guess
            <br />
            where I am?
          </p>
        </div>

        {/* Explanation */}
        <p className="mb-6 text-sm text-slate-400">
          🎯 Guessing costs{" "}
          <strong className="text-yellow-400">1 point</strong>.
          <br />
          If you find me, you get{" "}
          <strong className="text-yellow-400">3 points!</strong>
        </p>

        {/* Guess */}
        <button
          onClick={onGuess}
          disabled={points < 1}
          className="mb-3 w-full rounded-xl border-2 border-yellow-400 bg-yellow-400 px-5 py-4 font-bold text-slate-950 transition hover:bg-yellow-300 disabled:cursor-not-allowed disabled:opacity-40"
        >
          🎯 Yes! Let me guess!
          <span className="ml-2 text-sm">(-1 ⭐)</span>
        </button>

        {/* Skip */}
        <button
          onClick={onSkip}
          className="w-full rounded-xl border-2 border-slate-600 bg-slate-800 px-5 py-4 font-bold text-white transition hover:border-yellow-400 hover:bg-slate-700"
        >
          🙈 No thanks, show me!
        </button>

        <p className="mt-6 text-xs italic text-slate-500">
          "Hehe... good luck finding me! 🐾"
        </p>
      </div>
    </div>
  );
}