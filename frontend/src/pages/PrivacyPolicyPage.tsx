const h2 = 'mt-8 text-lg font-semibold text-slate-100'
const p = 'mt-2 text-sm leading-relaxed text-slate-400'
const li = 'mt-1 ml-5 list-disc text-sm leading-relaxed text-slate-400'

export function PrivacyPolicyPage() {
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-slate-100">Privacy Policy</h1>
      <p className={p}>
        Last updated: 2026-07-24. Chat 42 ("Moulinette") is a student project built as part of the 42 school
        curriculum (ft_transcendence). It is not a commercial service. This page explains what data we collect
        while you use it and how it's handled.
      </p>

      <h2 className={h2}>1. What we collect</h2>
      <ul>
        <li className={li}>Account data: your email address, and a securely hashed password if you sign up directly.</li>
        <li className={li}>
          If you sign in with 42 OAuth instead, we receive your 42 login and 42 email address from 42's API — we
          never see or store your 42 password.
        </li>
        <li className={li}>Photos you upload of campus cats, and the map zone you tag them with.</li>
        <li className={li}>
          Activity needed to run the app's features: friends list, sighting history, and gamification stats
          (achievements, leaderboard scores).
        </li>
      </ul>

      <h2 className={h2}>2. Photos and people in them</h2>
      <p className={p}>
        Uploaded photos are meant to be of cats, but may incidentally include people in the background. Every
        upload is run through an automated cat-detection filter; photos that don't contain a cat are rejected and
        not stored. We aim to minimize what identifiable image data we keep — where practical, we favor keeping
        only the detection result and a thumbnail rather than the full original. As a school project, this
        handling is best-effort, not a certified enterprise process — please avoid uploading photos where a
        person's face is the main subject.
      </p>

      <h2 className={h2}>3. How we use your data</h2>
      <ul>
        <li className={li}>Building the shared campus cat map: sighting locations, timestamps, and history.</li>
        <li className={li}>
          Generating Moulinette's AI-written diary entries and question answers, based on aggregated real
          sighting data (not your personal account details).
        </li>
        <li className={li}>Friends, notifications, and the "guess where the cat is" leaderboard game.</li>
      </ul>

      <h2 className={h2}>4. Cookies</h2>
      <p className={p}>
        We set a single essential cookie to keep you signed in (an HTTP-only, secure session token). We don't use
        advertising or third-party tracking cookies.
      </p>

      <h2 className={h2}>5. Third parties</h2>
      <p className={p}>
        We talk to 42's API (api.intra.42.fr) if you use "Continue with 42" to sign in. If the AI features call an
        external language-model API, only the sighting data needed to generate a response is sent — never your
        password or session token.
      </p>

      <h2 className={h2}>6. Data retention & deletion</h2>
      <p className={p}>
        You can delete your account at any time from your profile; this removes your login credentials and
        personal profile data. Sighting records you contributed to the shared map may be retained in anonymized
        form so the map and cat history stay intact for other users.
      </p>

      <h2 className={h2}>7. Security</h2>
      <p className={p}>
        Passwords are hashed with bcrypt and never stored in plain text. All traffic between your browser and our
        servers is encrypted over HTTPS.
      </p>

      <h2 className={h2}>8. Who this is for</h2>
      <p className={p}>
        Chat 42 is built for 42 students and campus visitors. It's evaluated as part of a school project and run
        on infrastructure managed by the project team, not a commercial hosting provider.
      </p>

      <h2 className={h2}>9. Changes to this policy</h2>
      <p className={p}>
        If this policy changes, we'll update the date at the top of this page.
      </p>

      <h2 className={h2}>10. Contact</h2>
      <p className={p}>Questions about this policy can be sent to the project team via your 42 campus contacts.</p>
    </div>
  )
}
