# Scope: Laurel Hill classifier-gateway agent (Experienced track)

A fast classifier acts as a gateway that runs on every incoming message. An LLM acts as a specialist that is called only when a handler needs to write something.

## Flow
1. **Message arrives.** The classifier runs once and answers several questions together: message type, priority tier, emergency yes/no, possible fraud yes/no, language, and which open ticket (if any) it follows up on.
2. **Code routes by the result,** using a table:
   - **Emergency:** one LLM call drafts the call script to Luis, the text to the after-hours vendor, and the safety reply to the tenant. Deadline is received time plus 1 hour.
   - **Leasing:** the LLM drafts a reply using `units.csv` and `showing_slots.csv`.
   - **Routine maintenance:** a template and a work order, with no LLM call.
   - **Rent, legal or ESA:** a short summary for Priya, with no reply to the tenant.
   - **Suspected fraud:** flagged for Priya with no LLM call, and no action taken.
   - **Low confidence:** goes to a human queue with the probabilities shown.

## Why this design
- **Speed:** emergencies get classified in a fraction of a second, which matters against a 1-hour deadline.
- **Narrower context:** each handler's LLM call gets only the handbook section it needs, which usually gives better drafts.
- **Fewer LLM calls:** routine and fraud messages never reach an LLM.
- **Audit trail:** every decision has a stored probability, so the supervision screen can show why a message went where it did.
- **Pitch material:** "X% of messages needed no LLM call" with a number from the replay.

## Risks to design around
- **Silent misroutes:** a wrong classification sends a message to the wrong handler with no second check. Use a confidence cutoff, a keyword override for gas, carbon monoxide and fire, and a sampled review list on the supervision screen.
- **Untrusted text:** the LLM only produces drafts. Code or a person performs every action.
- **Setup time:** the build window is 60 minutes and a classifier API key may not be quick to get. Build the router with an LLM as the classifier first, behind one function, and swap Jev (Typesafe's System One classifier) in if the key works.

## Stretch goal
The Monday 7:00 AM "what would still be overdue" view.

## Stack
Python with a simple web page.

## Data
Track files are in the Experienced folder: `company.md`, `messages.csv`, `units.csv`, `vendors.csv`, `showing_slots.csv`, `response_history.csv`.
Pitch number: leasing leads answered in under an hour got a tour 11 of 21 times, against 8 of 92 after more than a day.
