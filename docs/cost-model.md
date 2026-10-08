# Cost and efficiency model (Experienced track, Laurel Hill Residential)

Purpose: compare an event-driven classifier gateway with the approaches other teams are likely to build.

Labels used throughout:
- (D) comes from the track data files.
- (S) comes from a cited source, listed at the bottom, with the date it was checked (Oct 8, 2026).
- (A) is our assumption. Say so out loud when presenting.

## The approaches compared

1. **Naive polling agent.** A timer wakes an LLM agent every N minutes. It loads the inbox, classifies each message with an LLM using the full handbook and data, and acts. The LLM runs on every wake-up, even when no mail arrived.
2. **Smart polling agent.** A timer checks the inbox in plain code and calls the LLM only when new mail exists. One LLM call per message, with the full handbook and data, doing both classification and the follow-up work.
3. **Classifier gateway (ours).** Each message triggers a fast classifier on arrival. Code routes on the result. An LLM is called only by handlers that need to write something, with only the context that handler needs. The agent drafts and a person acts.

Approach 2 is the fair comparison for cost. Approach 1 shows what happens with a naive design.

## Inputs

### Volume and mix (D: response_history.csv, 960 messages, Apr 1 to Sep 30, 183 days)
- About 157 messages a month (5.2 a day).
- Leasing 40.5%, routine maintenance 39.1%, rent/payment 8.8%, other 7.8%, emergency 3.9%.
- 61% of messages (leasing, emergency, rent, other) need an LLM-written draft. Routine maintenance (39%) uses a template and a work order.
- 74% of messages arrive outside Monday to Friday, 9 AM to 6 PM (our definition of after hours).
- 27 of 37 emergencies (73%) got a first response after more than 1 hour. The SLA in company.md is 1 hour.

### Prices (S)
- Gemini 2.5 Flash, paid tier: $0.30 per million input tokens, $2.50 per million output tokens. Output includes thinking tokens. Cached input is $0.03 per million, plus $1.00 per million tokens per hour of cache storage.
- Gemini 2.5 Flash-Lite: $0.10 input, $0.40 output per million.
- Jev (Typesafe classifier): $0.042 per million input tokens, output free. 64K context. Listed on OpenRouter as typesafe/jev-1.13 with 0.17 s median latency. No free tier is documented, and access started as an early-access waitlist on Sep 15, 2026.

### Token sizes (A, estimated at 4 characters per token from file sizes)
- Static context: company.md 1,350 + units.csv 2,500 + vendors.csv 200 + showing_slots.csv 650 = 4,700 tokens, plus about 150 for the message, so about 4,850 tokens input per full-context call.
- Full-context call output: 400 tokens (classification plus draft), thinking off or minimal.
- Empty polling run (approach 1 only): 3,000 tokens input (system prompt, tool definitions, inbox listing) and 150 tokens output.
- Gateway handler call: 1,500 tokens input (only the relevant handbook section and data) and 300 tokens output.
- Classifier call: 1,600 tokens input (label descriptions plus the message).
- To replace these estimates with measured counts, run the Gemini countTokens call on the real prompts.

## 1. Response latency (math, no assumptions about tokens)

Detection delay is the time between a message arriving and the agent seeing it.

| Approach | Average wait | Worst case | Share of the 1-hour emergency SLA used before any work starts |
|---|---|---|---|
| Poll every 60 min | 30 min | 60 min | 50% on average, 100% worst case |
| Poll every 15 min | 7.5 min | 15 min | 12.5% on average, 25% worst case |
| Poll every 5 min | 2.5 min | 5 min | 4% on average, 8% worst case |
| Event-driven gateway | seconds | seconds | about 0% |

Why it matters for leasing (D): tour booking rate by first response time, with 95% Wilson intervals.

| First response | Tours booked | Rate | 95% interval |
|---|---|---|---|
| Under 1 hour | 11 of 21 | 52% | 32% to 72% |
| 1 to 4 hours | 33 of 78 | 42% | 32% to 53% |
| 4 to 24 hours | 37 of 198 | 19% | 14% to 25% |
| Over 24 hours | 8 of 92 | 9% | 5% to 16% |
| All leasing | 89 of 389 | 23% | 19% to 27% |

The under-1-hour sample is small, so quote the range. The trend across all four rows is consistent. This is a correlation, since fast replies and booking could share causes.

## 2. API cost per month, one customer (A on tokens, S on prices)

| Approach | LLM calls a month | Cost a month |
|---|---|---|
| 2. Smart polling, LLM on every message | 157 | $0.39 |
| 3. Classifier gateway | 96 | $0.13 |
| 1. Naive polling every 60 min | 157 plus 720 empty runs | $1.30 |
| 1. Naive polling every 15 min | 157 plus 2,880 empty runs | $4.06 |
| 1. Naive polling every 5 min | 157 plus 8,640 empty runs | $11.40 |

Gateway savings: about 67% vs smart polling, 90% vs hourly naive polling, 97% vs 15-minute naive polling, 99% vs 5-minute naive polling. LLM calls fall 39% vs either polling design.

Sensitivity:
- **Thinking tokens.** Gemini 2.5 Flash bills thinking as output. If each LLM call spends 1,000 extra thinking tokens, smart polling costs about $0.78 and the gateway about $0.37, a 53% saving. Set the thinking budget low for classification and drafting.
- **Context caching does not help at this volume.** Storing 4,850 tokens in an explicit cache for a month costs about $3.54 in storage, while the discount on 157 messages saves about $0.21.
- **Scale.** At 100 customers: gateway about $13 a month, smart polling about $39, naive polling every 15 minutes about $406, every 5 minutes about $1,140. Naive polling cost grows with customer count and poll frequency even when mail is quiet.

Honest framing: against a sensible polling design, the API saving is about 26 cents a month per customer. The reason to build it this way is latency, fewer model calls, narrower context and control. Do not pitch API dollars as the main benefit.

## 3. Staff time (A on minutes, S on wage)

- Wage: median pay for property, real estate and community association managers is $33.65 an hour (BLS, May 2025 data). This is raw pay with no overhead added. Leasing and maintenance staff may earn less.
- By hand: 157 messages times minutes per message. With the agent: routine maintenance 15 seconds, leasing review 1 minute, emergency 2 minutes, rent and other summaries 3 minutes, about 2.85 hours a month in total.
- Minutes per message by hand is our estimate. Replace it with Priya's or Jake's number if you can get one.

| Minutes by hand per message | Hours by hand | Hours saved | Value at $20 an hour | Value at $33.65 | Value at $45 |
|---|---|---|---|---|---|
| 3 | 7.9 | 5.1 | $101 | $171 | $228 |
| 5 | 13.2 | 10.3 | $207 | $348 | $465 |
| 8 | 21.1 | 18.3 | $365 | $614 | $821 |

This saving applies to any approach that drafts replies. It is the baseline benefit, and the sections above are what we add.

## 4. Leads and deadlines

- Leasing leads a month: about 64 (D). Current tour rate 23% (D). If every lead were answered inside an hour at the observed 52%, that would be about 19 more tours a month. Using the low end of the interval (32%) gives about 6, and assuming only half the gap is causal gives about 9. Quote it as "roughly 6 to 19 more tours a month, upper bound".
- Average rent across all 140 units is $1,773 a month (D: units.csv), so one lease is about $21,300 a year in rent. We have no tour-to-lease conversion, so we do not claim a lease count.
- Emergencies: 73% miss the 1-hour SLA today (D). The gateway drafts the call and text in seconds, so the only delay left is the person calling.

## 5. Control and safety (what the Managed score rewards)

| | Agent that acts on its own | Classifier gateway |
|---|---|---|
| Action taken by | The LLM | A person or plain code |
| Mistake detection | Read the transcript afterward | Every decision has a probability, a low-confidence queue and a sampled review list |
| Gas, carbon monoxide, fire | Depends on the LLM reading it correctly | Keyword override forces emergency regardless of the classifier |
| Untrusted message text | Reaches an LLM that can act | Reaches an LLM that can only draft |
| Overdue view | Not usually built | Skip to Monday 7:00 AM shows what would still be overdue |

## 6. Price to quote

There is no source for what Laurel Hill would pay, so this is a judgment:
- Staff time saved is about $170 to $610 a month at the BLS wage, depending on minutes per message. The middle case (5 minutes) is about $350.
- A price near $300 a month sits below the middle case, before counting faster tours or the emergency SLA. At $300 a month, annual fees are about $3,600, which is about 17% of one year's rent on an average unit.
- Reference only: human answering services quoted by one vendor blog run $150 to $600 a month for phone-only message taking and per-minute rates of $0.75 to $1.50 (unverified vendor estimates, phone not email).

## 7. Pitch lines
- "73% of Laurel Hill's emergencies get a first response after the 1-hour deadline today (response_history.csv)."
- "A team that checks the inbox every 15 minutes spends up to a quarter of that deadline before it starts. We start in seconds."
- "Leads answered in under an hour booked a tour about half the time. After a day, about 9%. Overall it is 23%."
- "Our agent drafts and a person acts. Every decision shows its confidence, and anything below the cutoff goes to a human with the reason."
- "We make 39% fewer model calls than a message-by-message agent, and we never call a model on an empty inbox."

## Caveats to state
- Token counts are estimated from file sizes. Prices were checked on Oct 8, 2026 and can change.
- Jev access may require a waitlist or an OpenRouter key, so the demo needs an LLM fallback classifier.
- Minutes per message by hand and the agent review times are our estimates.
- Tour rate by response time is a correlation with a small sample in the fastest bucket.

## Sources (checked Oct 8, 2026)
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini 2.5 Flash on OpenRouter: https://openrouter.ai/google/gemini-2.5-flash
- Jev 1.13 on OpenRouter: https://openrouter.ai/typesafe/jev-1.13
- Jev pricing summary: https://www.layer3labs.io/guides/jev-pricing
- What is Jev (Browserbase): https://browserbase.com/blog/what-is-jev
- BLS wage data: https://www.bls.gov/ooh/management/property-real-estate-and-community-association-managers.htm
- Answering service price ranges (vendor blog, unverified): https://www.myaifrontdesk.com/blog-posts/how-much-does-an-answering-service-cost-in-2026
