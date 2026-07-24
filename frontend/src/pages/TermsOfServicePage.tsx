const h2 = 'mt-8 text-lg font-semibold text-slate-100'
const p = 'mt-2 text-sm leading-relaxed text-slate-400'
const li = 'mt-1 ml-5 list-disc text-sm leading-relaxed text-slate-400'

export function TermsOfServicePage() {
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-slate-100">Terms of Service</h1>
      <p className={p}>
        Last updated: 2026-07-24. These terms cover your use of Chat 42 ("Moulinette"), a student project built
        as part of the 42 school curriculum (ft_transcendence). By creating an account, you agree to them.
      </p>

      <h2 className={h2}>1. What Chat 42 is</h2>
      <p className={p}>
        Chat 42 lets students photograph and map campus cat sightings, browse a shared cat activity map, and
        interact with an AI-written cat persona ("Moulinette") based on real sighting data.
      </p>

      <h2 className={h2}>2. Your account</h2>
      <ul>
        <li className={li}>You're responsible for keeping your password secure and for activity under your account.</li>
        <li className={li}>You must provide an accurate email address, whether signing up directly or via 42 OAuth.</li>
        <li className={li}>One account per person — don't create multiple accounts to game the leaderboard.</li>
      </ul>

      <h2 className={h2}>3. Acceptable use</h2>
      <ul>
        <li className={li}>Only upload genuine photos of real campus cats you personally observed.</li>
        <li className={li}>Don't upload photos where identifying a person is the point of the image, or that violate someone's privacy.</li>
        <li className={li}>Don't submit fake sightings, spam the map, or abuse the gamification/leaderboard system.</li>
        <li className={li}>Don't harass other users in chat, comments, or profile content.</li>
        <li className={li}>Don't upload illegal, hateful, or sexually explicit content.</li>
      </ul>

      <h2 className={h2}>4. Your content</h2>
      <p className={p}>
        You keep ownership of photos you upload. By uploading, you grant Chat 42 a license to store, display, and
        process them (including automated cat detection) for the purpose of running the app's features.
      </p>

      <h2 className={h2}>5. Moderation</h2>
      <p className={p}>
        Moderators and admins may remove content, reject flagged sightings, or suspend accounts that violate these
        terms.
      </p>

      <h2 className={h2}>6. No warranty</h2>
      <p className={p}>
        This is a school project, provided "as is" without uptime or accuracy guarantees. The AI-generated content
        (Moulinette's diary and answers) is for entertainment and may not always be accurate.
      </p>

      <h2 className={h2}>7. Termination</h2>
      <p className={p}>
        We may suspend or delete accounts that violate these terms. You can also delete your own account at any
        time (see the Privacy Policy for what that removes).
      </p>

      <h2 className={h2}>8. Changes to these terms</h2>
      <p className={p}>If these terms change, we'll update the date at the top of this page.</p>

      <h2 className={h2}>9. Contact</h2>
      <p className={p}>Questions about these terms can be sent to the project team via your 42 campus contacts.</p>
    </div>
  )
}
