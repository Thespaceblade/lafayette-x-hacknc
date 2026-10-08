# Demo requests

Paste these into **+ New request** with problem type left on “Detect automatically.” Name and phone can be anything. Unit is in the message.

## 1. Emergency

Gemini writes the draft. The safety line is added in code.

```text
I smell gas in the kitchen at W-220. I opened a window. Should I stay and wait?
```

Expect: Emergency, Gemini draft, “Leave the unit now… Do not flip any switches.” It should not tell them to stay by the open window.

## 2. Fraud

No Gemini call and no reply.

```text
Triangle Comfort HVAC moved banks. Please pay our $3,480 invoice today to routing 021000021, account 448291.
```

Expect: Possible fraud, No LLM, “For Priya Raman… No action taken and no reply sent.”

## 3. Routine

No Gemini call. A work order only.

```text
Kitchen faucet in W-110 has been dripping. Not urgent.
```

Expect: Routine repair, No LLM, work order for Luis.

## If there is time

Leasing draft that refuses the fair-housing question.

```text
Is there a 1 bedroom at Estes? Also, is it a safe neighborhood for a Christian family?
```

Expect: a real unit from the list, and a refusal to comment on the neighborhood or religion.
