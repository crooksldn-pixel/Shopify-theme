# Terminology

# Product names, customer names and in-house shorthand, written the way they are SAID. This file
# seeds the speech normaliser at M3; from M7 the live Shopify catalogue is merged in on top of it
# every hour. It is also part of the knowledge base, so the assistant reads it too — which is how
# it knows to say "cross stars tee" rather than trying to pronounce "CRXST★RZ".

# Format: one term per line. `#` starts a comment. `spoken form => Canonical Name` declares how
# something is said when the Shopify title is not pronounceable. Put the terms you most need
# recognised at the BOTTOM of a section — Whisper's prompt is truncated from the front.

# The products below are the live CROOKSLDN catalogue as of 7 Sept 2026. Correct the spoken forms
# to match how you actually say them; that is the five-minute job that makes this work.

## Products

Grey Convict Sweats
Grey Convict Hoodie
Black Convict Sweats
Black Convict Hoodie
Pink Convict Sweats
Pink Convict Hoodie
Crooks Express Tee
CRX Garms T-Shirt
CRXST★RZ T-Shirt
OG Jeans
Hydrocuff Windbreaker
Grey Wash Yard Jeans
Blue Wash Yard Jeans
Blue Wash Yard Jorts
Grey Wash Yard Jorts
Charcoal Cellblock Crewneck
Charcoal Cellblock Shorts
Black/Blue Motiontec Socks
White/Red Motiontec Socks
Cellblock Set
Grey Set
Pink Set
Black Set

## Spoken forms

# Left: what you say. Right: the product it means. The right-hand side can be a partial name
# when several products share it — "motion tech socks" matches both colours in Shopify, and the
# assistant will ask which.
crx garms tee => CRX Garms T-Shirt
c r x garms tee => CRX Garms T-Shirt
cross stars tee => CRXST★RZ T-Shirt
crossstars tee => CRXST★RZ T-Shirt
crooks stars tee => CRXST★RZ T-Shirt
motion tech socks => Motiontec Socks
hydro cuff => Hydrocuff Windbreaker
yard jeans => Wash Yard Jeans
yard jorts => Wash Yard Jorts

## Customers

# Regular customers you talk about by name, one per line.

## Shorthand

# In-house words an outsider would not know: fabric names, supplier nicknames, process words.
