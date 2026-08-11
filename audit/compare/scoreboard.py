#!/usr/bin/env python3
"""Extract the comparison matrix from evidence/. Run after the sweep; feeds REPORT.md."""
import json, os, sys, glob

EV = 'audit/compare/evidence'
tags = sorted(set(os.path.basename(f).rsplit('-', 1)[0] for f in glob.glob(f'{EV}/*.json')))
# tags like 'crooks-live-recon' split wrong; derive from known kinds instead
kinds = ['recon', 'perf', 'a11y', 'commerce', 'journeys']
tags = sorted(set(os.path.basename(f)[:-len('-recon.json')] for f in glob.glob(f'{EV}/*-recon.json')))

def load(tag, kind):
    p = f'{EV}/{tag}-{kind}.json'
    return json.load(open(p)) if os.path.exists(p) else None

rows = {}
for t in tags:
    r, pf, a, c, j = (load(t, k) for k in kinds)
    d = {}
    if r:
        d['platform'] = (r.get('home') or {}).get('platform')
        d['botWall'] = r.get('botWall')
        seo = (r.get('home') or {}).get('seo') or {}
        d['title'] = seo.get('title', '')[:60]
        d['metaDesc'] = bool(seo.get('metaDesc'))
        d['jsonLd'] = ','.join(str(x) for x in (seo.get('jsonLdTypes') or []))[:60]
        pseo = (r.get('pdp') or {}).get('seo') or {}
        d['pdpTitle'] = pseo.get('title', '')[:70]
        d['pdpMetaDesc'] = bool(pseo.get('metaDesc'))
        d['cookieBanner'] = (r.get('home') or {}).get('cookieBanner')
        d['overlays10s'] = len(r.get('overlaysAt10s') or [])
    if pf:
        for pg in ['home', 'pdp', 'pdpDesktop']:
            v = (pf.get('pages') or {}).get(pg) or {}
            if v.get('error'): d[pg] = 'ERROR'
            elif v:
                vit, tr = v.get('vitals', {}), v.get('transfer', {})
                d[pg] = {'lcp': vit.get('lcp'), 'cls': round(vit.get('cls', 0), 4), 'inp': vit.get('inp'),
                         'kb': tr.get('totalKB'), 'req': tr.get('requests')}
    if a:
        for pg in ['home', 'pdp']:
            v = (a.get('pages') or {}).get(pg) or {}
            if v and not v.get('error'):
                d[f'axe_{pg}'] = {'types': len(v.get('axeViolations') or []),
                                  'serious': len([x for x in v.get('axeViolations') or [] if x.get('impact') in ('critical', 'serious')]),
                                  'ids': [x['id'] for x in (v.get('axeViolations') or [])][:6],
                                  'zoomFail': (v.get('zoom') or {}).get('horizontalScroll')}
    if c:
        d['fv'] = (c.get('pdp') or {}).get('fv')
        d['sizeGuide'] = c.get('sizeGuide')
        d['delivery'] = c.get('delivery')
        d['soldOut'] = c.get('soldOutSignal')
        d['atc'] = c.get('addToCart')
        d['trustPages'] = {k: {kk: vv for kk, vv in (v or {}).items() if kk in ('status', 'placeholders', 'email')}
                           for k, v in (c.get('trustPages') or {}).items()}
    if j:
        P = j.get('personas') or {}
        d['p2_new'] = (P.get('p2_returningFan') or {}).get('newSignal')
        d['p3_table'] = (P.get('p3_sizeAnxious') or {})
        d['p4'] = (P.get('p4_sceptic') or {})
        d['p6_kbAtc'] = (P.get('p6_a11y') or {}).get('atcReachableByKeyboard')
        d['p7'] = (P.get('p7_slow') or {})
        d['p8'] = (P.get('p8_postPurchase') or {}).get('hunt')
        d['p9'] = (P.get('p9_comparison') or {}).get('spine')
        d['p10'] = (P.get('p10_gift') or {}).get('aff')
    rows[t] = d

print(json.dumps(rows, indent=1))
