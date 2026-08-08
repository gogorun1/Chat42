interface GameMenuProps {
  page: string;
  setPage: (page: string) => void;
}

export default function GameMenu({
  page,
  setPage,
}: GameMenuProps) {
  const buttons = [
    {
      id: "map",
      label: "Map",
      icon: "🗺",
    },
    {
      id: "history",
      label: "History",
      icon: "🐾",
    },
    {
      id: "heat",
      label: "Heat Map",
      icon: "🔥",
    },
    {
      id: "diary",
      label: "Diary",
      icon: "📖",
    },
    {
      id: "ranking",
      label: "Ranking",
      icon: "🏆",
    },
    {
      id: "report",
      label: "Report",
      icon: "➕",
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-800 bg-slate-950/95 px-4 py-3 backdrop-blur">

      <div className="mx-auto flex max-w-5xl justify-center gap-2 overflow-x-auto">

        {buttons.map((button) => (
          <button
            key={button.id}
            onClick={() => setPage(button.id)}
            className={`min-w-[80px] rounded-xl px-3 py-2 text-center text-xs transition ${
              page === button.id
                ? "bg-amber-400 font-bold text-slate-950"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            <div className="text-lg">
              {button.icon}
            </div>

            {button.label}
          </button>
        ))}

      </div>

    </nav>
  );
}