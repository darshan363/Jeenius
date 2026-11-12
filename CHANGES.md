# What changed in this version

## Login, OTP and roles
- **Google login**: the page now signs in with a background request and moves on by itself (no manual refresh). Small clock differences no longer reject Google tokens.
- **Email OTP**: sends over HTTPS (Brevo or Resend) because Render's free plan blocks SMTP. Resend button has a 60 s countdown, the code box accepts pasted/auto-filled codes and submits at 6 digits, and clear messages appear when email is not configured. `OTP_PEPPER` is no longer required.
- **Forgot password** now works (email code -> new password). Google-only accounts can add a password this way.
- Unfinished sign-ups can be completed (code is re-sent). Failed-login throttling added.
- **Teacher <-> learner**: either role can be switched at any time from *My profile* (`/account-setup.html?edit=1`), the dashboard, the teacher plan page, or the profile box in chat. Learners must pick Class 8, 9 or 10.
- Pending-approval screen checks automatically every few seconds.

## Removed old code
`app.py` (unused Flask copy), the Aadhaar/age-provider module and its endpoints, the FDG and Tests screens (their script `/fdg.js` was missing and `/api/tests/sample` did not exist), parent-OTP stubs, unused CSS/JS, per-boot legacy data wipe.

## Animations
- Demo bars, auto-play demos, example text, "try it" steps and how-to lists removed everywhere.
- Every animation now ends with a live line: **IF (control) a -> b  =>  (result) x -> y**, plus one short logic sentence.
- Newton's Laws replaced by three separate labs: **First Law** (bus, tablecloth, sliding ball), **Second Law** (your trolley vs a reference trolley), **Third Law** (skaters, balloon rocket, swimmer + wall).
- "Free Fall" folder renamed to `82-free-fall` (a folder name with a space broke links).
