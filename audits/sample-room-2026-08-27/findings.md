# Sample Room — 50-persona functional audit

**Subject:** https://sample-room-sync.base44.app (Base44 app `6a90446deba61e278de01664`)  
**Date:** 27 August 2026  
**Result: 0 clean passes / 24 partial / 16 broken / 10 missing. 24 blockers.**

The app is login-gated, so no persona could click through the UI. Each job was traced against live data, executed code (logic modules run under node with real inputs), and the source click path. No records were created or modified.

Full report with evidence: `report.html`. Method and persona briefs: `test-brief.md`.

---

## Make something

### P1 — Marcus, Brand owner · **PARTIAL** (Major)
*Task:* Type an idea in Make, get four realistic candidates to choose from

The button on /make generates nothing — it only creates a session and navigates. Inside the studio, "Show me four" does work and choosing one persists. But candidates is overwritten on every round, so each "Show me four more" permanently destroys the previous four, and the EARLIER ROUNDS panel can never render because the rounds array it needs is silently discarded by the server.

`MakeStudio.jsx:80 writes rounds; MakeSession.jsonc declares no such field; live record 6a9097c3… returns no rounds key`

> "Four turn up and I can pick one — but the button on the front page does nothing and the second I ask for four more the first four are gone for good."

### P2 — Dee, Designer · **BROKEN** (Blocker)
*Task:* Drop in three reference images and have the generation actually derive from them

References upload, persist and are sent to the function. The function then puts them in existing_image_urls — a parameter the Base44 SDK does not define and that appears nowhere in it. All the model reliably receives is one sentence: "Take colour, material and detailing cues from the supplied reference images." The 8-image brand reference library is not connected to Make at all.

`SDK 0.8.44 integrations.types.d.ts:61 — GenerateImageParams { prompt: string }; grep existing_image_urls in @base44/sdk → no hits; generateProductImage/entry.ts:92`

> "It uploads my three references, shows them back to me, then generates from a sentence that says 'use the references'."

### P3 — Marcus, Brand owner · **BROKEN** (Blocker)
*Task:* Put the CROOKSLDN logo on the thing he is designing, from inside Make

The picker is wired and lets you set placement, method and mm width — then all three go nowhere. The logo file rides the same unsupported parameter, so the model is told to "copy exactly" from an image it may never receive. marks is local React state with no field to save to, so the placement and size are lost on reload and never reach a Placement record.

`MakeStudio.jsx:20 useState; no marks field in MakeSession.jsonc; MarkPicker options filtered by o.url — all 5 Components have image:null`

> "There's a picker with my logo in it and boxes for where it goes and how wide — none of it reaches the picture or the spec."

### P4 — Sasha, Freelance designer · **PARTIAL** (Major)
*Task:* Bring in her own finished render instead of generating

The mechanism works but the UI points the wrong way. "I already have an image" opens no file picker; the empty state tells her to press "Show me four", which on an empty idea returns a 400 error, and that button is never disabled. Find the secondary "Use my own image" button and the path is sound all the way to breakdown.

`Make.jsx:94; MakeStudio.jsx:243-245, 168-174; generateProductImage/entry.ts:57`

> "I clicked 'I already have an image' and it dropped me on a screen telling me to press Generate, which then errors."

### P5 — Marcus, Brand owner · **MISSING** (Major)
*Task:* Edit the expanded brief before generating, as promised

No screen displays expandedBrief, let alone edits it. It is written once after each generation and never read. The generator is fed the raw idea box. expandArtworkBrief, the function that exists to draft such a brief, has zero call sites anywhere in the app.

`grep expandedBrief in src → one write at MakeStudio.jsx:80, zero reads; schema says "shown and editable before generating"`

> "It says the brief is shown and editable before generating — it's never shown, and my design is filed under a completely different product's name."

## Artwork, logos and vectors

### P6 — Nia, Graphic designer · **BROKEN** (Major)
*Task:* Generate a CROOKSLDN graphic from a prompt, in brand style

The pipeline holding the brand-style logic is unreachable — generateArtwork and expandArtworkBrief have no callers since the generator pages were deleted. The live substitute sends exactly one Brand field to the model: doNots. Tone, colours and fonts never reach the prompt, and the crafted style prose is discarded in favour of raw "era: 1970s." key/value strings.

`6 callFunction sites in src, neither is generateArtwork; ComponentStudio.jsx:103; artworkPrompt.js:63 styleLines() dead`

> "It knows three things we don't do and nothing about what we look like — that's not a brand style, that's a blocklist."

### P7 — Nia, Graphic designer · **BROKEN** (Major)
*Task:* Rely on the three brand negative constraints being enforced

The do-nots reach the prompt as text, but the post-generation "brand mark" check is a substring match on the prompt string, never on the pixels — rephrase and it passes while the model still draws lettering. The report is never persisted and the Approve button does not consult it. Setting any vectorFile short-circuits Resolution and Rendering to pass.

`guardrails.js:80-83, :30, :105; executed under node — prompt 'big block letters spelling the label name' → PASS on Brand mark`

> "It reads my prompt for the word CROOKSLDN and calls that a brand check, then cries about four pixels."

### P8 — Tom, Production artworker · **BROKEN** (Blocker)
*Task:* Place the real brand mark onto artwork as an asset, never redrawn

The compositing is real and produces a genuine flattened PNG. Everything that makes it usable is discarded: the handler keeps only the image and drops the logo id, mm width and x/y, and the Component schema has nowhere to hold them. It also overwrites the unmarked original. The mm size survives only as burnt pixels — the exact thing the factory asks for twice.

`CompositeMark.jsx:47-50 returns them; ComponentStudio.jsx:257 keeps only data.image; compositedLogoId null on all 124 GeneratedAssets`

> "It's welded someone's Helvetica mock-up into my print file, called it our lockup, and forgotten to write down how big it is."

### P9 — Tom, Production artworker · **BROKEN** (Blocker)
*Task:* Convert a PNG logo into a print-ready vector for the factory

The tracer itself is legitimate and emits real path geometry. The call site passes the whole return object where the SVG string was expected, so the uploaded .svg is the 15-byte text "[object Object]". That file becomes the factory's print-ready master and is flagged as a vector master — and its mere presence flips the guardrail checks to pass.

`ComponentStudio.jsx:228-229 svgToFile(obj); executed under node → File size 15, contents "[object Object]"; regression vs deleted ArtworkGenerator.jsx:186 which destructured correctly`

> "I pressed Convert to vector and it saved me a text file that says [object Object], then told the checks everything was fine."

### P10 — Nia, Graphic designer · **PARTIAL** (Major)
*Task:* Ask for four variations off a chosen graphic

"More like this" does pass the chosen image back through, so the intent is right — but it rides the same unsupported parameter as the references, so the conditioning is unproven. The lineage field parentAssetId is read and written by no code at all and is null on all 124 records. The four come back into ephemeral state, and choosing one overwrites the graphic she was varying from.

`grep parentAssetId → one hit, the schema line; generateComponent/entry.ts:75; Component holds a single image field`

> "Pick a favourite and it eats the one you started from, and there's no record of what came from what."

## Components onto garments

### P11 — Kofi, Designer · **PARTIAL** (Major)
*Task:* Generate a logo in Components, then see it on a garment

The path exists and is short, but the whole on-garment panel is gated behind the component having an image, and no component in the app has one. The preview it would give is not his spec anyway: it hardcodes six invented spots unrelated to the 17 real placements, defaults to a tee, and draws at a guessed scale. The four candidates live in React state only — nothing is saved.

`ComponentStudio.jsx:288 gate; OnGarment.jsx:6-13 hardcoded spots; grep GeneratedAsset.create in src → 0 matches`

> "I made four logos, picked one, and the app kept none of them."

### P12 — Kofi, Designer · **BROKEN** (Blocker)
*Task:* Break a finished design into reusable components

The image is never generated and never written. The breakdown asks a language model to describe what is on the design and then creates Component records from that text with no image key in the object at all — while the source design image sits right there unused. The parallel Artwork record is created with no source file either, so the placement's artwork is empty too.

`Breakdown.jsx:121-126 — create({name,kind,method,widthMm,heightMm,repeatCm,notes,derivedFromSessionId,status,brandId}), no image; Breakdown.jsx:128-130`

> "It read my design, wrote me a shopping list of what's on it, and then made five empty records."

### P13 — Priya, Product developer · **BROKEN** (Blocker)
*Task:* Attach an approved component to a placement

componentId saves, and nothing ever reads it. The placement resolves its picture solely through artworkId, so the component's artwork never appears — on screen or on pack page 08. The dedicated attach widget is dead code with zero importers. There are two half-connected artwork systems: the AI creates Components, while rendering, preflight and the pack all read Artwork.

`grep componentId in src → two writes, zero reads; Placements.jsx:115; AttachToPlacement.jsx has no importer; PlacementsPanel.jsx:66 reads p.offsetMm, a field that does not exist`

> "I attached the component, it saved an ID nothing looks at, and the factory gets a name and no picture."

### P14 — Priya, Product developer · **BROKEN** (Blocker)
*Task:* Check on the flats that placements sit in the right spot at the right size

The mm-to-pixel arithmetic is correct and it does draw real artwork. Everything downstream is wrong: anchor is never read, so a hem tag draws 20mm below the shoulder; horizontalRef is never read; and wearer's-left is flipped to a negative x, drawing on the viewer's left while the pack prints the opposite rule beside it. On live data nothing draws at all — 9 of 11 artworks have no file.

`Executed flatRender geometry under node: anchor=Hem and anchor=HPS both y=85.8; From side seam and From CF both x=409.7; wearer's left x=345.2, left of centre`

> "The drawing and the words underneath it disagree — I can't send this to anyone."

### P15 — Wei, QC engineer, Guangzhou · **PARTIAL** (Major)
*Task:* Read the placement spec to set up the print — needs the logo measurements

The gate genuinely works: preflight refuses to issue a pack with a placement missing width, height, anchor or offset, and the written sentence is correct and complete. So he will not get a blank dimension. What he gets is a correct sentence next to a drawing that contradicts it — which is the phone call this app exists to stop.

`Executed runPreflight against the live 'Thigh logo' record → blocks on widthMm, heightMm and art; format.js:24-28 sentence is correct`

> "The numbers are complete, but the picture beside them puts the logo on the wrong side — so I still ring London before I burn a screen."

## The pack and its outputs

### P16 — Marcus, Brand owner · **MISSING** (Blocker)
*Task:* Export the multi-page PDF tech pack to email the factory

There is no PDF generation anywhere. jspdf and html2canvas sit in package.json and are imported by zero files. No window.print, no print stylesheet, no download of any kind — the pack is 13 article elements scrolling in a browser. Each page is overflow:hidden inside a locked A4 box, so any table taller than the box is silently clipped rather than flowing on.

`grep for jspdf/html2canvas imports in src and base44 → nothing; both TechPackVersion records have pdfFile:null; Versions.jsx:58 prints NOT ATTACHED on every row`

> "There's no PDF — I'm meant to email a factory in China a link to a login screen they can't get into."

### P17 — Ade, Production manager · **MISSING** (Blocker)
*Task:* Get the Excel BOM and measurement spec

No spreadsheet library exists in the project and xlsxFile is written by no code path. Worse, the app tells the user otherwise: the preflight screen reports "…1 workbook" as a hardcoded literal with nothing behind it. No BOM is assembled in one place either — fabric sits on page 06, labels on 12, packaging on 13, and no page anywhere carries a quantity or consumption figure.

`Preflight.jsx:50 hardcodes '1 workbook'; grep xlsxFile → one read, zero writers; both versions have xlsxFile:null`

> "It tells me to my face that it made one workbook, and there isn't a line of code in the app that can write a spreadsheet."

### P18 — Ade, Production manager · **MISSING** (Blocker)
*Task:* Get one zipped folder, structured and named, for the factory's drive

No zip library, no archive code, no file download of any kind. readmeFile and driveFolderUrl are aspirational schema fields nothing writes, so the "Copy link" button gated on driveFolderUrl can never appear. And there is almost nothing to collect by hand: 9 of 11 artworks have no print-ready file, and the only two that do are SVG boxes reading PLACEHOLDER.

`grep download/createObjectURL/new Blob in src → only a local upload preview; no function emits a file; PackBuilder.jsx:125 apologises that nothing was written to Drive`

> "Three of the four things we're supposed to send don't exist as files, and the two artworks that do are grey boxes with PLACEHOLDER printed on them."

### P19 — Wei, QC engineer, Guangzhou · **PARTIAL** (Blocker)
*Task:* Read page 04, the construction page

The waffle really is gone — the hardcoded seam rows are deleted, an empty table prints "Not specified" rather than inventing, and generation is per-product. But no live garment has any construction data, so every garment pack in the app prints a blank page 04, and nothing stops it being issued: preflight has zero construction rules. Meanwhile the same invent-a-spec defect moved down the pack — the decoration page still hardcodes cure temperatures and mesh counts.

`Executed runPreflight on a product with construction:[] → 9 blocks, none mentioning construction; PagePreview.jsx:301-311 hardcodes 'Cure 160 °C for 60 s', 'Mesh count 110T', 'Density 0.4 mm'`

> "Page 04 is honest now — it says nothing on every garment you've got — and page 11 still tells me cure temperatures nobody typed in."

### P20 — Marcus, Brand owner · **PARTIAL** (Major)
*Task:* Run preflight, issue v1, and get a frozen snapshot

Preflight genuinely blocks — it disables the button and re-runs before writing, throwing before anything is created. The diff works. But the snapshot is 22 flat strings that omit most of the pack: no seam rows, no dimensions, no care symbols, no carton or AQL terms, no images. And nothing ever re-renders a pack from a snapshot, so the pages a factory was sent silently change the moment settings are edited.

`Executed preflight → 9 blocks, 5 warnings, readiness 3/7; snapshot probe → 22 fields, 'any key holding a seam row? false'; grep PagePreview → only PackBuilder, always from live records`

> "The checks stop me sending rubbish — but what it freezes is twenty-two lines of text, not the pack I actually sent."

## The factory's side

### P21 — Wei, QC engineer, Guangzhou · **PARTIAL** (Major)
*Task:* Read the tech pack in Chinese

The Chinese that exists is fully populated — all 120 glossary terms and every POM name have CN. But the CN layer stops at labels: 23 plain headers against 11 bilingual ones, and every free-text field he actually needs is English-only with no CN field in the schema at all — including howToMeasure, the measuring instructions themselves. The bilingual "do not measure from this" caption exists but only prints when there's a hero image, which 11 of 13 products lack.

`SizeChart.jsonc points[] has pomNameCN but no howToMeasureCn; PagePreview.jsx:54-55 caption inside the heroImageUrl branch; the else branch at :57-63 has no caption in either language`

> "The column titles are in Chinese and the measuring instructions are in English — that is backwards."

### P22 — Mrs Chen, Factory sample room manager · **PARTIAL** (Blocker)
*Task:* Get composition, weight, width and a colour reference before cutting

The numeric fabric spec is real and complete — all 24 swatches carry composition, gsm and width, and the pack prints them. The colour half fails: 23 of 24 swatches have no photo, so the cell prints NO PHOTO, and the one that has a photo is a synthetic cream rectangle reading PLACEHOLDER — used as the swatch for the colourway named Jet Black. The pack never checks isPlaceholder, so it prints as if real.

`grep isPlaceholder in components/pack/ → zero hits; preflight.js:80 hard-blocks a missing photo but :153 only warns on a placeholder; SwatchDetail.jsx:82 never clears the flag on real upload`

> "You sent me a cream square labelled Jet Black and nothing says it's fake — so I'm emailing you for the swatch again."

### P23 — Ade, Production manager · **MISSING** (Major)
*Task:* Have the app recommend a manufacturer from the vetted list

There is no recommendation engine of any kind — capabilities and decoration methods are rendered as decorative chips and never compared to the product. Worse, the vetted list cannot be entered: Manufacturer is only ever listed, never created or updated, anywhere in the codebase. The two live records are seeded and one is a blank placeholder.

`grep 'Manufacturer.' in src → 7 hits, all .list(); grep recommend → zero hits app-wide; preflight only checks the id is set and the name isn't 'Unassigned'`

> "It's a phone book with one number in it, and I can't even add the second."

### P24 — Wei, QC engineer, Guangzhou · **PARTIAL** (Major)
*Task:* Check the pack's trade terms against the glossary

The glossary genuinely feeds the pack — every heading resolves through it. But it is wired only into the pack renderer: the product pages fetch all 120 terms and then no component reads them, so there is no inline gloss while specifying. And "confirmed by your factory" is inert — verifiedByManufacturer is written and read only inside the glossary page, and all 120 terms are unverified with nothing marking that on the pack.

`grep verifiedByManufacturer → 6 hits, all in Glossary.jsx; ProductRecord.jsx:39 fetches terms, grep glossary in components/product/ → zero hits`

> "Not one of those 120 terms has been confirmed by us and the pack doesn't say so — so I still ring about 缝型 versus 车缝方式."

### P25 — Ade, Production manager · **BROKEN** (Minor)
*Task:* Confirm the pack honours the unit settings

Both unit settings are stored on the live record and read by nothing — a grep for either name across the whole src tree returns nothing. Every unit in the app is a hardcoded literal, and the settings screen prints a static uneditable sentence instead of the stored value. The output is correct today only because the literals happen to match; nothing would follow if the value changed.

`grep measurementUnitGarment|measurementUnitPlacement in src → no output; PackSettingsPage.jsx:101-102 prints a literal string while every other field uses the editable helper`

> "The pack says cm and mm and it's right — but that's luck, not the setting."

## Size charts and measurements

### P26 — Marcus, Brand owner · **MISSING** (Blocker)
*Task:* Load his existing size charts in from a spreadsheet

There is no import of any kind — no file input, no paste handler, no OCR, no CSV or XLSX parser in the tree. The only creation path makes a chart with an empty points array and sizes hardcoded to S–XXL, so denim waist sizes or a one-size cap cannot even be represented. Reproducing just the six charts already there is 486 hand-typed entries.

`SizeCharts.jsx:29 creates with sizes:['S','M','L','XL','XXL'], points:[]; UploadFile is wired into 15 places, none in sizecharts; counted 51 POMs × sizes = 231 value cells, each its own network write`

> "I said I'd load my charts in and the answer is a blank table and 486 boxes to type."

### P27 — Priya, Product developer · **PARTIAL** (Major)
*Task:* Add a POM, set tolerance, fill values across S–XXL

The edit loop works and persists, and tolerance is per-point. But there is no validation at all: a chest that shrinks from S to XXL saves clean, passes preflight clean and prints clean, because the only check anywhere tests for a missing value. The POM code is read-only once created, there is no delete or reorder, and every cell blur fires a whole-document write, so fast tabbing can race and drop values.

`PomTable.jsx:56-64 bare update, no checks; preflight.js:129 tests pt.values?.[sz] == null only; PomTable.jsx:103 renders pomCode as static text`

> "It'll happily let me type a garment that gets smaller as it gets bigger, and then print it."

### P28 — Marcus, Brand owner · **MISSING** (Major)
*Task:* Ask the AI to recommend changes to a size chart

No AI path touches a point of measure. There are six model call sites and none read or write a POM. The only producer of size-chart change proposals is a deterministic mapping that copies a measured value across after a human has already made the decision — so the chart changes only once a physical sample has come back and the owner has decided himself.

`grep InvokeLLM → 6 hits, none referencing points/POM/tolerance; loop.js:20-42 filters on decisions the user already chose; live SpecChangeProposal count: 0`

> "There is no AI anywhere near my charts, just a form that copies a number I already wrote down myself."

### P29 — Wei, QC engineer, Guangzhou · **BROKEN** (Blocker)
*Task:* Read the measurement spec for the mylar packaging pouch

The size chart is chosen by the model as free text and written with no validation. The pouch got the Denim — straight chart; its sibling record got the literal English word "none" stored as a foreign key. The printed page says "Overall size: Not specified" — a bag with no dimensions — while the version snapshot, the immutable spec of record, captures the full jeans table.

`breakDownDesign/entry.ts:42,106 guard is a prompt sentence only; Breakdown.jsx:165 persists verbatim; ran buildSnapshot on the live record → 49 of 56 fields are jeans measurements, 'ANY DIMENSIONS FIELD?: false'`

> "You have sent me a plastic bag with a 78 cm inseam and no bag size — I stop the line and we lose a week."

### P30 — Priya, Product developer · **BROKEN** (Blocker)
*Task:* Make a print scale with garment size, S versus XXL

scalesWithSize is stored, never computed, and settable nowhere — three occurrences in the whole app: two read-only displays and one hardcoded false. Nothing does the arithmetic. And the pack prints, unconditionally on every placement, a bilingual instruction telling the factory not to scale — a literal string, not a test of the field. The one thing the owner said every brand forgets, the app forgets too.

`grep scalesWithSize → 3 lines; Breakdown.jsx:140 writes false; PagePreview.jsx:290 prints 'Print size is identical on every garment size. Do not scale.' with no condition`

> "It's a field nothing can switch on, nothing does the maths for, and the pack says 'do not scale' regardless."

## The swatch library

### P31 — Marcus, Brand owner · **PARTIAL** (Major)
*Task:* Photograph and catalogue 40 swatches from the China trip

Strictly one at a time — the file input has no multiple attribute and there is no bulk import for swatches, though the app uses bulkCreate for references. "Add many" just resets the form, so supplier and source trip get retyped for every record. Nothing reads the photo: no colour extraction, no gsm estimate, no auto-fill. And a swatch flagged placeholder stays flagged forever, because the photo upload never clears the flag.

`AddSwatchForm.jsx:79 no multiple; SwatchDetail.jsx:82 writes {photo} only, vs PlacementDetail.jsx:56 which also clears isPlaceholder; 23 of 24 live swatches have photo:""`

> "I came back from Guangzhou with a suitcase of fabric and it wants me to type the same supplier name in forty times."

### P32 — Dee, Designer · **PARTIAL** (Major)
*Task:* Have the AI pick a fabric from the library rather than inventing one

The library genuinely is passed to the model and the match writes back a real swatch link — the wiring is real. But the model gets four text attributes and no image, so fabric is matched by reading words, never by looking; availableColours is never sent or checked, so nothing stops a green colourway on a black-only swatch; and the join is exact string equality, so one stray space degrades to "nothing matched".

`breakDownDesign/entry.ts:21,28,119 passes the library; Breakdown.jsx:95 matches with === ; grep availableColours → written once, read nowhere downstream`

> "It does look at my swatches, but it's reading a text list with the lights off."

### P33 — Mrs Chen, Factory sample room manager · **PARTIAL** (Major)
*Task:* Source against the swatch photo and full spec on the fabric page

The chain resolves and the spec prints. But the photo prints at 40 pixels square — not something anyone can colour-match against. Blank composition and gsm print as silently empty cells rather than "not specified". And placeholder status never reaches the pack: the fabric page uses a raw image, not the component that carries the PLACEHOLDER badge, so a generated beige square prints as if photographed.

`PagePreview.jsx:232 width:40,height:40; :234 raw {s.composition} with no fallback; grep isPlaceholder in components/pack/ → zero hits`

> "A forty-pixel square is not a colour reference, and an empty box in the composition column tells me nothing."

### P34 — Marcus, Brand owner · **PARTIAL** (Major)
*Task:* At 300 swatches, find black heavyweight loopback, 380gsm+, from the Dongguan supplier

Real filtering exists and pagination will hold at 300. Half his query lands: loopback and the weight range work. "Black" fails outright — colour is not in the search haystack and there is no colour filter, which is the single most obvious way to search a swatch library. "Dongguan" fails — there is no city or region field. There is also no sort control and the weight slider is capped at 600gsm.

`Swatches.jsx:46 haystack is code+name+composition only; schema has no location field; :23 lists with no explicit limit, unlike every other swatch consumer in the app`

> "I can find the loopback and the weight, but I can't ask it for black — which is the entire reason I keep a swatch library."

### P35 — Dee, Designer · **BROKEN** (Blocker)
*Task:* Get the colourway to mean something — own code, Pantone, tied to a swatch

The read side is wired and the colourway does drive the flat's colour. The write side collapses. dyeMethod is read in three places and written in none, so every colourway the app creates has it permanently null with no UI to fix it. Codes are minted by chopping the colour name to six letters — JETBL, MATTE — beside the house CW-01 scheme, with no uniqueness check. And the Pantone is a guess the model read off a photo, printed to the factory in full ink as though confirmed.

`grep dyeMethod → 3 reads, 0 writes; Breakdown.jsx:112 code = name.slice(0,6); :114 pantoneTcx = bodyColour.pantoneGuess; live now has two Jet Blacks, CW-01 and JETBL`

> "It named my colourway JETBL by chopping the word in half and printed a Pantone it guessed off a photo as if it were confirmed."

## The sampling loop

### P36 — Ade, Production manager · **PARTIAL** (Major)
*Task:* Request a sample round against the issued pack

For the SKU asked about there is no path — Convict Joggers has no tech pack version, so the button is disabled. Where a pack exists the binding to the version is correct and hard. Courier is absent from the request form. And nothing leaves the app: the field labelled "Note to the factory" saves to the database with no email, export or copy control anywhere, so the factory never sees the request.

`SampleRounds.jsx:48-53 disabled; grep mailto|clipboard|download on the sample path → nothing; RequestRound.jsx:41 seeds sizes M,L for every product, so a one-size cap creates zero measurement rows`

> "The note I just wrote to Vivian sits in a database she'll never open."

### P37 — Priya, Product developer · **PARTIAL** (Major)
*Task:* Measure the returned sample against spec and tolerance

The tolerance maths is correct — executed across negative deviations and the boundary-equal case, it passes every one — and spec values come from the issued pack's snapshot rather than the live chart, which is right. The reporting is wrong: unmeasured rows count in the denominator as failures, so the same round reads "7 of 16" on one screen and "88%" on another. The measure screen applies no ordering, so POMs arrive in API order.

`Executed samples.js → boundary ±tol inTol=true, fp trap handled; live round has 16 rows, 8 measured; MeasurementsPanel.jsx:31 vs PerformancePanel.jsx:82`

> "The sums are right but the scoreboard isn't — 7 of 16 when I only measured 8."

### P38 — Priya, Product developer · **PARTIAL** (Major)
*Task:* Log a fault with photos, severity and a link to the placement or POM

The form writes every field needed and the shape works. Two real defects in the photos: every upload failure — network, auth, format — is reported to the user as "were too large", and on a partial failure the record is created anyway and the form stays open, so pressing Save again logs a duplicate fault instead of retrying. There is no way to attach a photo after the fact, and the Chinese description must be typed by hand.

`IssueForm.jsx:19-28 catch reports size for every error; :29-43 creates unconditionally then only closes on full success; IssuesPanel.jsx:52-58 read-only`

> "If a photo won't go up it tells me it was too big when it wasn't, and the only way to retry is to log the fault twice."

### P39 — Marcus, Brand owner · **BROKEN** (Blocker)
*Task:* Accept three measurements as made so round 2 is judged against the truth

He cannot. The decision dropdown is disabled on any measurement inside tolerance — which is the opposite of what "accept as made" is for — and the live round has one row out of sixteen outside tolerance. Nothing has ever reached the proposal stage. When the apply path does run it writes into the shared master chart used by three products, changes one size in isolation with no re-grade: executed, it made L identical to XL and edited the beanie's chart at the same time.

`MeasurementsPanel.jsx:84 disabled={inTol !== false}; live SpecChangeProposal count 0; executed ProposalsPanel apply → T02 L=74.5=XL; chart …926e5 is shared by Lock-Up Tee, Association Tee and Isolation Beanie`

> "It won't let me sign off the measurements that were fine, and when I made it run the sum it turned my L into my XL."

### P40 — Ade, Production manager · **PARTIAL** (Major)
*Task:* Judge the factory — reject rate, rounds to approval, lead time actual vs quoted

The figures are genuinely computed from real history, not placeholders. But there is one round in the app and it has never been closed, so two of four figures are em-dashes, and there is no reject-rate figure at all — the thing actually asked for. The one number shown, 88%, counts only measured rows and contradicts what the samples list prints for the same round.

`Executed PerformancePanel logic on live data → rounds 1, approval —, accuracy 88%, lead 17 vs 18 quoted, reject rate not computed anywhere`

> "Real sums on one seeded sample — no reject rate, two dashes, and an 88% the samples page calls 7 out of 16."

## Learning the brand

### P41 — Marcus, Brand owner · **MISSING** (Blocker)
*Task:* Have the app pull live Shopify sell-through to ground its recommendations

There is no Shopify code, no credentials, no connector and no sales field anywhere. The recommendation backend states the absence itself in a comment and then tells the model outright: "You have no sales data." Shopify is not even in the 82-connector catalogue for this app, so it cannot be connected.

`grep shopify across /app → 0 hits; generateConcepts/entry.ts:5 '// No sales data — that is Phase 5'; entry.ts:46; list_connectors → connected_count 0`

> "There is not one line of Shopify in this thing — it has never seen a single sale of mine."

### P42 — Marcus, Brand owner · **MISSING** (Blocker)
*Task:* Upload past tech packs and product files so it learns the house standard

Every file input in the app is image-only and there is no document parsing of any kind. The reference library is the sole brand intake. Worse, the one input with no filter is the brand logo uploader, and because it treats .pdf as a vector format, a tech pack dropped there is silently listed as a valid vector logo asset.

`AddReferenceForm.jsx:50 accept="image/*"; grep pdfjs/pdf-parse/application-pdf/ExtractDataFromUploadedFile → none; BrandProfile.jsx:9 VECTOR_FORMATS includes 'pdf'`

> "It will take a JPEG of a wall and call it brand learning, but it cannot read the three tech packs that define how we make things."

### P43 — Dee, Designer · **PARTIAL** (Major)
*Task:* Maintain the brand profile and have it steer generation

All six fields save, and three of them genuinely reach the models — tone, do-nots and colours. The other three are decoration: default print methods, blank suppliers and fonts are read nowhere outside the page that renders them. The two with the most manufacturing consequence are the dead ones.

`doNots reaches 5 functions; defaultPrintMethods only at BrandProfile.jsx:102,106; blankSuppliers only at :98; fonts only at :94`

> "Half of what I keep updating goes into the model and half just sits there — and it's the print method and the blanks that do nothing."

### P44 — Dee, Designer · **BROKEN** (Blocker)
*Task:* Tag moodboards by role so each steers generation differently

The reference library is written, listed and deleted — and read by nothing else in the app. It appears zero times in the backend. The role field is stored and consumed by no code at all. And the form tells the user the opposite: it states each reference is "passed to the artwork generator", which no generator receives.

`grep BrandReference across src and base44 → 4 hits, all its own CRUD; AddReferenceForm.jsx:64-68 makes the claim; 7 of 8 live records have no role key at all`

> "I tagged every board Style or Colour like it mattered, and the code never once opens that table."

### P45 — Marcus, Brand owner · **PARTIAL** (Major)
*Task:* Get suggestions grounded in sell-through, range gaps and the drop calendar

One of the three bases is real. The range is genuinely passed and the model reasons off it by name. Sales data is absent. The calendar is reduced to a bare drop name — launch dates exist on the records and are never sent. And the suggestions persist nowhere: nothing writes a ProductConcept, so the list is gone on refresh.

`Suggestions.jsx:27-31 sends products and dropName only; grep launchDate → display only; grep ProductConcept in src → 0 hits`

> "It can see my product list and that's it — and the suggestions vanish the second I refresh the page."

## Naming, drops, compliance, versions

### P46 — Ade, Production manager · **BROKEN** (Blocker)
*Task:* Rely on the naming convention for codes, artwork files and folders

Codes are a free-text suggestion with no format, length or uniqueness check, and the generator does not reproduce his house style — 5 of 8 real SKUs come out wrong. The breakdown path hardcodes the CRK- prefix, so the second brand would get CRK codes too. The file half does not exist: no filename is constructed anywhere, because nothing is ever exported.

`Executed slugify on his SKUs → CRK-CONVICT-JOGGERS vs real CRK-CONVICT-JOGGER, CRK-ASSOCIATION-TEE vs CRK-ASSOC-TEE; Breakdown.jsx:157 hardcodes 'CRK-'; colourway codes auto-generate as MATTE, JETBL beside house-style CW-01`

> "It guesses a code I'd have to retype every time, and there's no file to name because nothing ever comes out of it."

### P47 — Marcus, Brand owner · **MISSING** (Blocker)
*Task:* Set up his named heist-themed drops

There is no way to create or edit a drop — the page is a read-only table with no form, no button and no dialog, and the entity is never created or updated anywhere in the app. The three drops that exist were seeded. And although season is optional in the schema, the UI prints it as the drop's identity line, so his named drops read "Lock-Up · SS 2026".

`grep Drop.create|Drop.update in src → zero; Drops.jsx:51,67,80 render season and year as identity`

> "I can't add a drop at all, and the three in there are labelled with the season codes I specifically said we don't use."

### P48 — Ravi, Compliance ops · **PARTIAL** (Blocker)
*Task:* Specify neck label, care label with UK composition, swing tags and poly bag

He cannot create a trim — the page is read-only apart from one field, and the only create is inside the AI breakdown. Composition validation is real and does gate issue, but its fibre list is missing prescribed UK names and it rejects legitimate labels: any shell/lining garment, any decimal percentage, and the standard "exclusive of trimmings" wording. Care symbols are display-only with no write path at all.

`Executed composition.js → REJECT on 'Shell: 100% nylon, Lining: 100% polyester', '99.5% cotton, 0.5% elastane', '98% cotton, 2% elastane, exclusive of trimmings'; fibre list length 30, missing modacrylic and others; grep careSymbols → 4 hits, all reads`

> "It calls composition legally required and then refuses the composition on half my range, and I can't touch a single wash symbol."

### P49 — Priya, Product developer · **PARTIAL** (Blocker)
*Task:* Issue v2 and see exactly what changed from v1

The diff is genuinely computed and v1 really is frozen. But the snapshot is blind to whole sections: change the stitch density, add a seam row, reword the construction notes, change a wash symbol or swap the hero image and the diff reports nothing changed. Renaming a placement produces four phantom rows instead of one rename, because the diff key is the placement's name.

`Executed snapshot.js on two specs with 10 deliberate changes → 4 detected, 24 snapshot keys, no keys matching seam/spi/stitch/symbol/image; live v2 changeSummary is the string "df"`

> "It'll tell me the hem measurement moved but not that I changed the stitch density — and there's no actual pack to send either way."

### P50 — Sasha, Freelance designer · **PARTIAL** (Major)
*Task:* Land cold, find her way around, and stand up the performance claims

Navigation is genuinely fine — 15 destinations in three named groups, and the dashboard's "needs attention" rows link straight to the screen that fixes each thing. Two of three performance claims hold: 64 lazy chunks are real, and the dashboard query limits were cut. But the dashboard still runs preflight for every product, which downloads full-resolution artwork one file at a time just to read its pixel dimensions.

`Measured entry 441,026 B raw / 144,725 B brotli; Floor.jsx:59 runs runPreflight per product; preflight.js:95 awaits measureImage inside a sequential loop; 8 unbounded .list() calls with no brand filter`

> "I could find my way around fine, but the dashboard sat there pulling down print artwork one file at a time before it would show me anything."
