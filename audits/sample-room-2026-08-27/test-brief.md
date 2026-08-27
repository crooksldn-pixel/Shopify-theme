# SHARED BRIEF — Sample Room persona test (CROOKSLDN / Threads Alliance)

## What you are testing
Base44 app "Sample Room" — https://sample-room-sync.base44.app
Base44 appId: `6a90446deba61e278de01664`

VERIFIED FACT: the deployed live site is built from the CURRENT source in the Base44 sandbox
(live chunk `fn-ZKyzQ1gR.js` contains the fn.js unwrap helper; the old hardcoded seam rows
"overlock/coverstitch" are gone; 66 code-split chunks). So the sandbox source == what the user
clicks. Auditing the source IS auditing the live app.

The whole app is behind ProtectedRoute -> /login (src/App.jsx). Nobody can drive the UI in a
browser without the owner's credentials. So evidence comes from three places, in this order of
strength:
  1. LIVE DATA — what actually persisted in the user's real app (`query_entities`). Strongest.
     A null field in a real record proves a pipeline drops data.
  2. EXECUTED CODE — run pure logic modules under node in the sandbox (`run_command`).
     src/lib/*.js (guardrails, preflight, packPages, flats, composition, snapshot, readiness,
     samples, format, vectorise, imageOps, flatRender) are mostly importable without React.
  3. SOURCE TRACE — follow the actual click path through real files, cite file:line.
NEVER assert behaviour you have not traced to a line of code or a live record.

## Tools
Load with ToolSearch first:
  ToolSearch("select:mcp__Base44__read_file,mcp__Base44__grep,mcp__Base44__list_directory,mcp__Base44__query_entities,mcp__Base44__run_command")
Every call needs appId `6a90446deba61e278de01664`. App root is `/app` (use run_command with
absolute paths; `cd` does not persist).

STRICTLY READ-ONLY. Do NOT use write_file/edit_file/update_entities/create_entities/edit_base44_app.
Do NOT create test records — this is the user's live production data.
Prefer read_file/grep. Use run_command for node experiments and multi-file reads.

## App map
Pages (src/pages): Floor(dashboard) Products ProductRecord PackBuilder Preflight Versions
VersionDetail SampleRounds RequestRound SampleRound Measure Make MakeStudio Breakdown Components
ComponentStudio References Flats Glossary PackSettingsPage Swatches SwatchDetail SizeCharts
SizeChartDetail Placements Trims Manufacturers Drops BrandProfile Login Register etc.
Components (src/components): brand/ create/ flats/ floor/ make/ manufacturers/ pack/ placements/
product/ products/ references/ samples/ sizecharts/ sr/ swatches/ trims/ ui/
Logic (src/lib): guardrails preflight packPages flats flatRender composition snapshot readiness
samples format vectorise imageOps artworkPrompt labels loop glossary rendering fn AuthContext
Backend (base44/functions): breakDownDesign expandArtworkBrief generateArtwork generateComponent
generateConcepts generateConstruction generateConstructionRows generateProductImage locateInImage
Entities (28): Product Component Placement Artwork GeneratedAsset MakeSession Swatch SizeChart
SampleRound SampleMeasurement SampleIssue SpecChangeProposal TechPackVersion PackSettings
Manufacturer Trim Colourway Drop Brand BrandLogo BrandColour BrandFont BrandReference
GarmentFlat GlossaryTerm ProductConcept ConstructionProposal User

## Ground truth already established (do not re-derive, DO build on it)
- Component records (4 live): every one has image=null, printReadyFile=null, vectorFile=null.
  Two were created by "Separate" off a MakeSession breakdown.
- Placement: 16 live. Only the 2 from the breakdown have componentId. The seeded 14 have
  artworkId but no componentId. "Thigh logo" has widthMm=null, heightMm=null.
  Every single one has scalesWithSize=false.
- BrandLogo: only 2 records, both synthetic `data:image/svg+xml` Helvetica placeholders seeded by
  the app ("CROOKSLDN" set in Helvetica), marked isVector=true, minWidthMm 40/12.
  The user's REAL logos are PNGs and were never loaded.
- GeneratedAsset: many artworks with real images + guardrailReport running (resolution/rendering/
  method/brand-mark checks). vectorFile is null on all of them.
- MakeSession (4): one "Broken down" with 4 real generated candidates; one "Built" -> Product.
  One session titled "A raw denim pair of jeans" whose idea text is about mylar cat bags.
- Product "Standing Cat Mylar Pouch" (an Accessory) was auto-assigned sizeChartId
  6a904ade02a582c48cd926e9 — the SAME chart as "Yard Denim" — and construction=[].
- BrandReference: 8 records, images present and persisting.

## What the app is SUPPOSED to do (the spec you are polling against)
From the owner's requirements:
- Users: internal now, multi-brand later.
- Upload design -> realistic version; also CREATE the design (graphics from a prompt in brand
  style, whole product concepts, variations off an existing design, garment construction/
  silhouette design).
- Manufacturer receives ALL of: multi-page PDF tech pack; print-ready artwork files at correct
  size/format; one zipped folder, structured + named; Excel BOM + measurement spec.
- Manufacturer recommendations come from the owner's own vetted list.
- Learns brand from: live Shopify pull, uploaded past tech packs/product files, a brand profile,
  moodboards/reference images.
- Product types at launch: cut & sew, headwear + accessories, denim/outerwear/heavy technical,
  print-on-blank.
- Size charts: owner has existing charts to load in; AI may recommend changes.
- Naming convention: owner supplies it. Named drops (heist-themed), NOT season codes.
  Colourways get their OWN code. Real SKUs exist e.g. Convict Joggers, Yard Denim.
- Accuracy matters more than good looks. AI drafts everything, owner edits every field.
- "Recommend what to make" reasons from Shopify sell-through, gaps in range, drop calendar.
- Must specify labelling/trims/packaging: neck label/woven tag, care label + composition + UK
  compliance, swing tags + packaging.
- Nothing pushes anywhere else — tech pack + folder is the end of the line.
- The two things the factory ALWAYS has to ask for twice: LOGO MEASUREMENTS and COLOUR SWATCHES.
  The owner has a large physical swatch library collected in China to photograph and catalogue.
- Factory works in English and Chinese. Logos are PNG only. Manufacturer digitises embroidery
  (no DST files), but getting digitised would be good.
- Known gaps the owner was warned about: PNG-only logos (no vector master), and no fixed
  placement dimensions grid.

## The owner's own complaints (test these hardest — they are the reason for this exercise)
1. "the reference thing doesnt work"
2. "some images dont follow through"
3. "make something doesnt really allow for adding of logos etc"
4. "it also needs to think how the logos are used"
5. "on the generate logos etc you need to be able to port them over to see how theyd look on garment"
6. "alot of functionality is broken ... i dont think it does what you think it does"

## Output format — return EXACTLY this, nothing else
For each of your 5 personas:

### P<number> — <persona name>, <role>
**Task attempted:** <the concrete thing they tried to do, one line>
**Verdict:** WORKS | PARTIAL | BROKEN | MISSING
**What actually happens:** <2-4 sentences, mechanical, no praise>
**Evidence:** <file:line refs and/or live record fields. At least one hard citation. If you ran
code, give the command and the actual output.>
**Severity:** Blocker | Major | Minor | Cosmetic  (Blocker = the factory gets something wrong or
the owner cannot complete the job at all)
**Persona's verdict in their own words:** "<one sentence, in character, blunt>"

Verdict definitions — be strict:
- WORKS = the persona completes the task and the output is correct and usable downstream.
- PARTIAL = completes but the output is incomplete, wrong in a way they'd notice, or needs
  manual rework.
- BROKEN = the UI offers it but it fails, saves nothing, or produces wrong data.
- MISSING = there is no path in the app to do it at all.
A feature that exists but produces null/empty downstream is BROKEN, not PARTIAL.
Do not grade generously. The owner explicitly said the app does not do what the last agent
claimed it did.
