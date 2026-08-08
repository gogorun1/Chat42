interface Zone {
id: string;
name: string;
floor: string;
}

interface GuessCatProps {
zones: Record<string, Zone>;
onGuess: (zoneId: string) => void;
onSkip: () => void;
}

export default function GuessCat({
zones,
onGuess,
onSkip,
}: GuessCatProps) {
return ( <div className="mx-auto max-w-2xl">

```
  <div
    className="
      rounded-2xl
      border
      border-yellow-400/30
      bg-slate-900
      p-6
      shadow-xl
    "
  >

    {/* ================= TITLE ================= */}

    <div className="text-center">

      <p
        className="
          text-sm
          font-semibold
          uppercase
          tracking-widest
          text-yellow-400
        "
      >
        🎯 Guess Challenge
      </p>

      <h2 className="mt-2 text-3xl font-bold">
        Where is Moulinette?
      </h2>

      <p className="mt-3 text-slate-400">
        Choose the zone where you think Moulinette is hiding.
      </p>

      <div
        className="
          mt-4
          inline-flex
          rounded-full
          border
          border-yellow-400/30
          bg-slate-800
          px-4
          py-2
          text-sm
        "
      >
        ⭐ Cost: 1 point
      </div>

    </div>


    {/* ================= ZONE CHOICES ================= */}

    <div className="mt-8 grid gap-3 sm:grid-cols-2">

      {Object.keys(zones).map((zoneId) => {

        const zone = zones[zoneId];

        return (
          <button
            key={zoneId}
            onClick={() => onGuess(zoneId)}
            className="
              rounded-xl
              border
              border-slate-700
              bg-slate-800
              px-4
              py-4
              text-left
              font-semibold
              transition

              hover:border-yellow-400
              hover:bg-slate-700
              hover:text-yellow-400
            "
          >

            <span className="text-lg">
              📍
            </span>

            <span className="ml-2">
              {zone.name}
            </span>

            <span className="mt-1 block text-xs text-slate-500">
              Floor {zone.floor}
            </span>

          </button>
        );

      })}

    </div>


    {/* ================= SKIP ================= */}

    <button
      onClick={onSkip}
      className="
        mt-6
        w-full
        rounded-xl
        border
        border-slate-700
        bg-slate-950
        px-4
        py-3
        text-slate-400
        transition
        hover:bg-slate-800
        hover:text-white
      "
    >
      ← Skip guessing
    </button>

  </div>

</div>


);
}
