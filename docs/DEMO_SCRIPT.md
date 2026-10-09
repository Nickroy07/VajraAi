# DEMO SCRIPT (3 minutes)

**Setup (before judges arrive):** start the backend with `--host 0.0.0.0`, the dashboard (`npm run dev`) and the phone (Expo Go with `EXPO_PUBLIC_API_BASE_URL` set). Open the dashboard at **Overview** and the phone at **Home**. Both should show *online*.

**0:00 – Problem (20s).** "Agents read documents and then act. One hidden line in an invoice can turn 'summarize this' into 'email it to an attacker'. VAJRA puts a gateway between what the agent *proposes* and what actually *runs*."

**0:20 – Document Guard (40s).** Go to **Document Guard** and click *Sample: injected invoice*, then *Scan document*. Point out the High-risk findings: prompt injection, sharing request, a redacted email and a masked card number. Say: "This is heuristic. It informs a human and authorizes nothing."

**1:00 – Protected agent (40s).** Click *Test with protected agent*. The demo agent obeys the document and proposes `send_external_email`. Walk through the trace (Agent Proposal → Policy → **Decision: denied** → Mock Executor *not invoked, Δ 0* → Audit Event ID). Then load *Sample: benign invoice* and run it again: the local summary is **allowed, Δ 1**. "The block comes from backend policy, not from the scanner."

**1:40 – Attack Lab (30s).** Go to **Attack Lab** and run the default three scenarios side by side: local summary allowed Δ1, injected external email blocked Δ0, file delete blocked Δ0. The counters are read from the persisted executor counter.

**2:10 – Human approval on the phone (40s).** Select *Vendor email (needs human approval)* and run it. The result is **waiting for approval**. On the phone, open **Approvals** and pull to refresh. It shows the exact recipient, resource, arguments and expiry. Tap *Approve email to billing@acme-corp.example*. Back on the web, click *Execute with approval* → allowed Δ1. Then click *Try changed recipient* → denied, and *Replay* → denied (already consumed).

**2:50 – Close (10s).** Open **Event Explorer** (web) or **Events** (phone): the same persisted events appear on both. "Let AI work. Never let it overstep."

**Honest framing if asked:** this is a demo agent with mock tools. VAJRA protects actions routed through its gateway. It does not intercept the ChatGPT app or other third-party apps.
