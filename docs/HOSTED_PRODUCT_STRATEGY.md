# Neurocache: Hosted Multi-User Product Strategy

Product analysis for making Neurocache maximally effective as a hosted web app that others can sign up for, onboard into, and quickly see value from.

**Target audience:** Developers and technical users first (portfolio showcase, comfortable with API keys), then knowledge workers (Notion/Readwise users who want AI over their notes).

**Cost model:** Hybrid — free tier with managed key (limited messages/day) + BYOK for unlimited. Balances accessibility with cost control.

---

## The Core Value Proposition

**"An AI that actually knows YOUR stuff."** Every general-purpose chatbot (ChatGPT, Claude) is a blank slate per conversation. Neurocache's differentiator is persistent, personalized retrieval across your accumulated knowledge — notes, books, research, ideas. The hosted version needs to deliver that "aha moment" as fast as possible: *the AI references something specific from YOUR notes that you'd forgotten about.*

---

## The Critical Metric: Time to First Wow

Everything should be optimized around minimizing the gap between "I just signed up" and "holy shit, this AI knows my stuff." Every friction point in that path loses users. The onboarding flow IS the product for first impressions.

---

## Knowledge Source Strategy (The Big Question)

### Obsidian — Won't Work As-Is for Hosted

The current architecture mounts a local vault via Docker volume (`${OBSIDIAN_VAULT_PATH}:/vault`). This fundamentally can't work for a hosted multi-user app. Options:

- **ZIP upload of vault export** — Works but high-friction. User has to find their vault folder, zip it, upload potentially hundreds of MB. Viable as a power-user option but bad as the primary path.
- **Obsidian has no public sync API** — There's no OAuth flow or REST API to pull vault contents. Obsidian Sync is encrypted end-to-end by design.
- **Desktop companion app** — An Obsidian plugin or local agent that syncs to Neurocache's cloud storage. Cool but very high engineering effort and adds a dependency.

**Verdict:** Keep Obsidian support as a "power user" option (ZIP upload or future plugin), but it can't be the primary onboarding path for a hosted app.

### Notion — Best Primary Integration

- **OAuth 2.0** with granular page-level permissions — user authorizes, you pull their content
- **Rich API** for reading pages, databases, blocks, comments
- **Huge user base** among knowledge workers, students, researchers — exactly the target audience
- **Structured data** — Notion's block model gives you clean markdown-convertible content
- **Incremental sync** — API supports `last_edited_time` filtering for efficient re-indexing
- **Fits the "second brain" narrative perfectly** — many Notion users already think of it this way

**This should be the primary "Connect your knowledge" integration.** One OAuth click and their entire workspace is available.

### Direct Upload — Universal Baseline

- Drag-and-drop markdown files, PDFs, text files (already partially built for PDFs)
- No external dependencies, works for everyone
- Good for users who keep notes locally or want to try the app with a few files
- Could support bulk upload (folder of .md files as a zip)

### Quick-Start / In-App Notes — Zero-Friction Entry

**This is the secret weapon for onboarding.** Before connecting any external source:

- Let users **paste text** directly into a "Quick Notes" area — an article they're reading, meeting notes, a braindump
- Let users **write notes directly in the app** — a simple markdown editor
- Even **paste a URL** and the app scrapes/summarizes it into a note

This means someone can see value in literally 60 seconds: paste some notes, ask the AI about them, get a response that references their content. Then they're motivated to connect deeper sources.

### Readwise — Perfect Fit for the Book Use Case

- REST API with OAuth
- Syncs highlights from Kindle, Apple Books, Pocket, articles, podcasts
- Maps directly to Neurocache's book-centric value proposition
- "All the highlights from every book you've read, searchable by an AI that understands context"
- Relatively small but passionate user base — exactly the type who'd love this app

### Google Drive — Wide Reach, Lower Signal

- OAuth integration, massive user base
- Good for documents, research papers, shared docs
- Lower signal-to-noise ratio than Notion (lots of junk in most people's Drive)
- Could support selective folder/file connection rather than whole Drive

### Apple Notes — Surprisingly Valuable, Hard to Access

- Many people's actual "notes" live here, not in Notion/Obsidian
- No public API — would need iCloud integration or export
- Probably defer this, but worth noting as a gap

---

## Recommended Onboarding Flow

### Step 1: Sign Up (10 seconds)
- **Google OAuth** (one click, no password to remember, covers 90% of users)
- Optional: GitHub OAuth (for developer audience), email/password
- Land directly in the chat interface — it works immediately as a normal AI chat

### Step 2: First Conversation (30 seconds)
- The chat works out of the box with web search (already built)
- A subtle but visible banner/sidebar prompt: **"Make me smarter — connect your knowledge"**
- Don't block the user from chatting. Let them experience baseline value first.

### Step 3: Connect Knowledge (2-5 minutes)
Present options in order of friction (lowest first):

1. **Quick Notes** — "Paste or type something you're working on" (textarea, immediate)
2. **Connect Notion** — "One click to import your workspace" (OAuth button)
3. **Upload Files** — "Drop markdown or PDF files" (drag-and-drop zone)
4. **Connect Readwise** — "Import your book highlights" (OAuth)
5. **Upload Obsidian Vault** — "Export and upload your vault" (power user)

### Step 4: First "Wow" Moment (immediately after sync)
- After even one source is connected and indexed, the chat system prompt should be aware
- Prompt the user to ask about something in their notes
- Or better: **proactively suggest** — "I just indexed 47 of your Notion pages. Try asking me about [topic detected in their notes]"
- Show source attribution clearly — "Based on your note 'Project Ideas (March 2024)'"

### Step 5: Progressive Depth
- As they use it more, suggest connecting additional sources
- Show a "Knowledge Base" dashboard: what's indexed, stats, topic clusters
- "You've asked about machine learning 12 times but have no notes on it — want to add some?"

---

## Features That Make This Impressive (Beyond Basic Chat + RAG)

### Tier 1: Must-Have for Hosted Launch

| Feature | Why It Matters |
|---------|---------------|
| **Auth (Google OAuth via NextAuth.js)** | Can't have multi-user without it. NextAuth is 1-2 days of work. |
| **Notion Integration** | Primary knowledge source for hosted users. OAuth + API is well-documented. |
| **Direct file upload** | Extend current PDF upload to support .md, .txt, bulk zip. Universal fallback. |
| **Quick Notes / paste** | Zero-friction path to value. Tiny feature, huge onboarding impact. |
| **Cloud file storage (S3/R2)** | Replace Docker volume mount. Users' files need to persist in the cloud. |
| **Per-user data isolation** | Already 80% built (user_id FK on everything). Need real auth to activate it. |
| **Usage limits / rate limiting** | OpenAI API costs scale with users. Need per-user quotas or BYOK (bring your own key). |

### Tier 2: Differentiators That Show Sophistication

| Feature | Why It Matters |
|---------|---------------|
| **Cross-reference discovery** | "Your note on X connects to your highlight from Book Y" — this is the magic no other chatbot does. Already in your roadmap. |
| **Inline citations with preview** | Click a citation, see the source note inline. Builds trust and demonstrates RAG quality. |
| **Knowledge base dashboard** | Visual overview: what's indexed, topic clusters, connection graph. Shows the "brain" growing. |
| **Readwise integration** | Perfect complement to book import. Passionate niche audience that will evangelize. |
| **Suggested first questions** | After indexing, analyze content and suggest 3-5 questions to demonstrate value. |
| **Multi-source attribution** | "From your Notion page + your book highlights + web search" — show the blend clearly. |

### Tier 3: Polish That Elevates

| Feature | Why It Matters |
|---------|---------------|
| **Conversation-aware knowledge gaps** | "You ask about X a lot but have no notes on it" — drives engagement loop. |
| **Shareable insights** | Share a particularly good AI response (with sources) as a link. Viral loop. |
| **Scheduled re-sync** | Notion/Readwise auto-sync daily so knowledge stays fresh without manual action. |
| **Google Drive integration** | Wider reach, more source types. |
| **Topic clusters visualization** | Interactive graph showing how your knowledge connects. Impressive visually. |
| **Export** | Download conversations, knowledge base summaries. Reduces lock-in anxiety. |

---

## Cost Model Considerations

OpenAI API costs are the elephant in the room for a hosted app:

- **Embeddings**: ~$0.02 per 1M tokens (cheap — bulk indexing is fine)
- **Chat completions (GPT-4o)**: ~$2.50-10/1M tokens (expensive — per-conversation cost)
- **Web search**: Per-query cost via OpenAI Responses API

Options:
1. **Free tier + paid plans** — N messages/day free, unlimited for paid users
2. **BYOK (Bring Your Own Key)** — User provides their OpenAI API key. Zero cost to you, but higher friction.
3. **Freemium with knowledge limits** — Free users get 1 source + 50 notes, paid gets unlimited
4. **Hybrid** — Free tier with your key (limited), BYOK option for unlimited

**Decision: Hybrid (both options).** Free tier with a managed key (e.g., 20 messages/day, 1 knowledge source) so anyone can try it immediately, plus BYOK for unlimited usage. This works well for the target audience — developers are comfortable with API keys and will appreciate the option, while the free tier lowers the barrier for knowledge workers discovering the app. The free tier also lets you control costs while the app gains traction.

---

## Technical Architecture Shifts for Hosted

| Current (Local) | Hosted |
|-----------------|--------|
| Docker volume mount for vault | S3/R2 for user file storage |
| Hardcoded demo user | NextAuth.js with Google/GitHub OAuth |
| Local PostgreSQL in Docker | Managed PostgreSQL (Supabase, Neon, RDS) |
| No rate limiting | Per-user quotas + rate limiting |
| Single-user file paths | User-scoped storage keys (`users/{id}/files/...`) |
| Obsidian vault validation | Multi-source connector pattern (Notion API, file upload, etc.) |
| Backend + frontend on localhost | Frontend on Vercel, backend on Railway/Fly.io |

---

## What Would Make Someone Say "This Is Impressive"

1. **The speed of value** — Sign up, paste some notes, ask a question, get an answer that references your notes. Under 2 minutes.

2. **The cross-reference moment** — AI draws a connection between two of your notes you hadn't thought of. This is the "second brain" promise delivered.

3. **Source transparency** — Every claim backed by a citation you can click and verify. Not a black box.

4. **The compound effect** — Each new source makes the whole system smarter. The dashboard shows your "brain" growing. You're motivated to add more.

5. **The blend** — One response that weaves together your personal notes, your book highlights, and fresh web search results. No other tool does this.

---

## Priority Order for Implementation

If building toward a hosted launch, this is the sequence that maximizes impact per unit of effort:

1. **Auth (NextAuth.js + Google OAuth)** — Unlocks multi-user. ~2-3 days.
2. **Cloud file storage** — Replace volume mount with S3/R2. ~2-3 days.
3. **Quick Notes (paste/write in-app)** — Fastest path to value for new users. ~1-2 days.
4. **Deploy** — Frontend on Vercel, backend on Railway/Fly.io, DB on Supabase/Neon. ~2-3 days.
5. **Notion OAuth integration** — Primary knowledge source for hosted users. ~1 week.
6. **Inline citations with preview** — Visual trust-builder. ~3-4 days.
7. **Knowledge base dashboard** — Show what's indexed, suggest questions. ~3-4 days.
8. **Readwise integration** — Book highlights import. ~3-4 days.
9. **Cross-reference discovery** — The "magic" feature. ~1 week.
10. **Suggested first questions post-indexing** — Onboarding polish. ~1-2 days.
