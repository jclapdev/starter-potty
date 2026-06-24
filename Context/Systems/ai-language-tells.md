# AI Language Tells: Catalog and Self-Check

_Reference for the always-on "Language (No AI Tells)" rule in `base-rules.md`. The rule there carries the short version; this file holds the full catalog with plain-word alternatives, the structural and tonal patterns, and the pre-send checklist. Load it on demand: when writing or reviewing a document. Not needed for every task._

_Policy: judgment guardrail, not a hard blocklist. Avoid these by default; a flagged word is fine when it is the accurate choice. Applies to all output, including casual chat. Em-dashes: nearly eliminate._

---

## 1. Vocabulary (single words)

Swap the AI-favored word for the plain one.

| Avoid | Use instead |
|---|---|
| delve into | look at, dig into, examine |
| underscore, highlight (overused) | show, stress |
| pivotal, crucial, vital | important, key, or cut |
| realm, landscape, sphere, arena (figurative) | area, field, or name it |
| harness, leverage (verb), utilize | use |
| facilitate | help, ease |
| illuminate, shed light on | explain, show |
| foster, cultivate | build, grow, encourage |
| navigate (figurative) | handle, work through |
| streamline | simplify, speed up |
| bolster | support, strengthen |
| embark, journey | start, process |
| unlock, unleash, unveil | open, release, show |
| elevate | raise, improve |
| robust | strong, solid |
| seamless | smooth |
| holistic | whole, complete |
| multifaceted, nuanced | complex, or name the parts |
| myriad, plethora | many |
| tapestry, mosaic, symphony (as metaphor) | cut the metaphor |
| testament (to) | shows, proof of |

## 2. Hype and buzzwords (usually cut entirely)

revolutionize, transformative, groundbreaking, cutting-edge, game-changing, innovative, state-of-the-art, next-level, world-class, unparalleled, supercharge, turbocharge, "stands as a testament to", "a beacon of", "rich cultural heritage", "enduring legacy". Corporate jargon: synergy, circle back, low-hanging fruit, move the needle, deep dive, leverage (noun).

## 3. Filler phrases and hedges

- Editorial openers: "It's worth noting that", "It's important to note", "It is important to remember", "Needless to say", "It goes without saying".
- Essence phrases: "At its core", "At the end of the day", "When it comes to", "In the world of", "In the realm of".
- Time clichés: "In today's fast-paced world", "In the ever-evolving landscape of", "Now more than ever", "In an age where".
- Hedges: "generally speaking", "broadly speaking", "to some extent", "arguably", "tends to", "in many ways". Cut them, or make a specific claim.
- Wrap-ups: "In conclusion", "In summary", "Ultimately", "All in all" tacked on to restate.

Frequency note: "it's worth noting" shows up far more in AI text than human text (one survey: about 31x), and "in today's digital age" about 24x. See sources.

## 4. Transitions (overused as decoration)

Furthermore, Moreover, Additionally, Consequently, Subsequently, Nevertheless, Notably, Importantly. Prefer no transition, or a plain one (also, but, so).

## 5. Structural tells

- **Rule of three:** three parallel adjectives, nouns, or clauses in a row ("clear, concise, and compelling"). Vary the count.
- **Negative parallelism:** "It's not just X, it's Y" / "not only X but also Y". Avoid.
- **False balance:** both-sidesing with no stance ("While critics argue X, supporters say Y").
- **Restated prompt:** opening a reply by repeating the question.
- **Tacked-on conclusion:** a final paragraph that repeats the body.
- **Uniform paragraphs:** every section the same length, each opening with a transition.

## 6. Tone tells

- Promotional or marketing voice in a neutral context ("plays a vital role", "a wide range of").
- Relentless positivity and over-qualification.
- Vague attribution: "studies show", "experts say", "it is widely believed", with no source.
- Over-explaining the obvious; defining terms no one asked about.

## 7. Formatting and punctuation tells

- **Em-dashes:** the signature tell, and Claude overuses them. Nearly eliminate. Replace with commas, periods, or parentheses; keep one only when nothing else works.
- Title-case headings on every short section; colon-title constructions ("Unlock Your Potential: A Guide to…").
- Bold scattered across key terms throughout a passage.
- Emoji in professional or neutral text.
- Bulleting content that should be prose.

## 8. Sycophancy and chat tells

"Great question!", "Certainly!", "Absolutely!", "You're absolutely right", "I'd be happy to", "I hope this helps", "Let me…", "Feel free to", "Dive in", "Let's explore", "Happy to help".

---

## Pre-send self-check

Run before delivering any written work:

1. Search the draft for section 1 and section 2 words. Replace or cut.
2. Count em-dashes. Convert each to a comma, period, or parentheses unless nothing else works.
3. Find any "It's worth noting / At its core / In today's" filler. Cut.
4. Check for the rule-of-three cadence and "not just X, it's Y". Rewrite.
5. Check the opening sentence: does it restate the prompt? Cut.
6. Check the ending: is it a summary that repeats the body? Cut.
7. Read the first word of each paragraph: do several share the same transition? Vary them.

For long or high-stakes documents, run through the full checklist carefully before sending. The vault-verify hook catches word-level tells automatically; this checklist covers structural and tonal patterns it can't detect.

---

## Sources

- Wikipedia, *Signs of AI writing*: [en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Grammarly, *Common Words and Phrases in AI-Generated Text*: [grammarly.com/blog/ai/common-ai-words](https://www.grammarly.com/blog/ai/common-ai-words/)
- *Linguistic Characteristics of AI-Generated Text: A Survey* (arXiv 2510.05136): [arxiv.org/pdf/2510.05136](https://arxiv.org/pdf/2510.05136)
- Rolling Stone, *'ChatGPT Hyphen': Are Em Dashes a Giveaway of AI Writing?*: [rollingstone.com](https://www.rollingstone.com/culture/culture-features/chatgpt-hypen-em-dash-ai-writing-1235314945/)
- NPR, *Wikipedia editors publish guide to detect AI writing*: [npr.org](https://www.npr.org/2025/09/04/nx-s1-5519267/wikipedia-editors-publish-new-guide-to-help-readers-detect-entries-written-by-ai)

_Last updated: June 2026._
