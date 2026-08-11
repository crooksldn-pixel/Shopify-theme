#!/usr/bin/env python3
"""Aggregate panel verdicts -> data/aggregate.json + printed funnel/identity tables."""
import json, glob, os, statistics, math
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
personas = {p['id']: p for p in json.load(open(f'{ROOT}/data/personas.json'))['personas']}
cap = json.load(open(f'{ROOT}/data/capture-index.json'))

verdicts, compares, bad = [], [], []
for f in sorted(glob.glob(f'{ROOT}/data/verdicts/batch-*.jsonl')):
    is_cmp = '-compare' in f
    for i, line in enumerate(open(f)):
        line = line.strip()
        if not line: continue
        try:
            d = json.loads(line)
            (compares if is_cmp else verdicts).append(d)
        except Exception as e:
            bad.append((f, i, str(e)[:80]))

print(f'verdicts={len(verdicts)} compares={len(compares)} malformed={len(bad)}')
for b in bad[:5]: print('BAD', b)

BUY_INTENTS = {'buy-now', 'gift-hunt'}
def intent(pid): return personas[pid]['intent']
def device(pid): return personas[pid]['device']

def atc_step_n(theme, journey, dev):
    s = cap['themes'].get(theme, {}).get(journey, {}).get(dev)
    if not s: return None
    for st in s['steps']:
        if 'after-atc' in st['label']: return st['n']
    return None

def reached_atc(v):
    p = personas[v['persona_id']]
    if p['journey'] not in ('j1','j2','j3','j5'): return None
    if v['task'].get('completed'): return True
    ab = v['task'].get('abandoned_at')
    n = atc_step_n(v['theme'], p['journey'], p['device'])
    if ab is None: return True
    # abandoned_at may be a label; find its n
    s = cap['themes'].get(v['theme'], {}).get(p['journey'], {}).get(p['device'])
    abn = None
    if s:
        for st in s['steps']:
            if isinstance(ab,str) and (st['label'] in ab or ab in st['label']): abn = st['n']; break
    if abn is None or n is None: return False
    return abn > n

def pct(a, b): return f'{100*a/b:.0f}%' if b else '-'

agg = {'by_theme': {}, 'identity': {}, 'preference': {}, 'notes': {}}
for theme in ('old', 'new'):
    tv = [v for v in verdicts if v['theme'] == theme]
    seg = {}
    def block(vs):
        if not vs: return {}
        comp = [v for v in vs if v['task'].get('completed')]
        buy = [v for v in vs if intent(v['persona_id']) in BUY_INTENTS]
        buy_done = [v for v in buy if v['task'].get('completed')]
        atc = [v for v in vs if reached_atc(v) is True]
        atc_elig = [v for v in vs if reached_atc(v) is not None]
        steps = [v['task'].get('steps') for v in vs if isinstance(v['task'].get('steps'), (int, float))]
        trust = [v['trust'].get('score') for v in vs if isinstance(v['trust'].get('score'), (int, float))]
        ret = [v for v in vs if v.get('would_return') is True]
        sea = [v for v in vs if personas[v['persona_id']]['journey'] in ('j2', 'j7')]
        sea_done = [v for v in sea if v['task'].get('completed')]
        ab_stage = Counter(str(v['task'].get('abandoned_at')) for v in vs if not v['task'].get('completed'))
        sev = Counter()
        for v in vs:
            for fr in v.get('friction', []): sev[fr.get('severity')] += 1
        return {
            'n': len(vs), 'completed': pct(len(comp), len(vs)),
            'atc_rate_shopping_intents': pct(len(atc), len(atc_elig)),
            'checkout_reach_buy_intents': pct(len(buy_done), len(buy)),
            'median_steps': statistics.median(steps) if steps else None,
            'search_success': pct(len(sea_done), len(sea)) if sea else '-',
            'mean_trust': round(statistics.mean(trust), 2) if trust else None,
            'would_return': pct(len(ret), len(vs)),
            'abandon_stages': dict(ab_stage.most_common(8)),
            'friction_by_severity': {str(k): v for k, v in sorted(sev.items(), key=lambda x: str(x[0]))},
        }
    seg['overall'] = block(tv)
    for d in ('mobile', 'desktop'):
        seg['device_' + d] = block([v for v in tv if device(v['persona_id']) == d])
    for it in ('buy-now', 'research-compare', 'browse-graze', 'returning', 'gift-hunt', 'lookup-support'):
        seg['intent_' + it] = block([v for v in tv if intent(v['persona_id']) == it])
    agg['by_theme'][theme] = seg

    # identity
    words = Counter()
    fs_adj = Counter()
    for v in tv:
        for w in v.get('brand_recall', {}).get('three_words', []) or []:
            if isinstance(w, str) and w.strip(): words[w.strip().lower()] += 1
        for w in v.get('five_second', {}).get('adjectives', []) or []:
            if isinstance(w, str) and w.strip(): fs_adj[w.strip().lower()] += 1
    feels = Counter(v.get('five_second', {}).get('feels_like', '?') for v in tv)
    price = Counter()
    for v in tv:
        g = str(v.get('five_second', {}).get('price_guess', '')).lower()
        for bkt in ('luxury', 'premium', 'mid', 'cheap', 'budget'):
            if bkt in g: price[bkt] += 1; break
        else: price['other/' + g[:20]] += 1
    whom = [str(v.get('five_second', {}).get('for_whom', ''))[:80] for v in tv]
    total_words = sum(words.values())
    top5 = sum(c for _, c in words.most_common(5))
    agg['identity'][theme] = {
        'recall_words_top15': words.most_common(15),
        'five_second_adjectives_top15': fs_adj.most_common(15),
        'distinct_recall_words': len(words),
        'top5_concentration': round(top5 / total_words, 2) if total_words else None,
        'feels_like': dict(feels),
        'price_guess': dict(price),
        'for_whom_sample': whom[:20],
        'product_remembered': Counter(str(v.get('brand_recall', {}).get('product_remembered', ''))[:40].lower() for v in tv).most_common(8),
        'price_remembered': Counter(str(v.get('brand_recall', {}).get('price_remembered', ''))[:20] for v in tv).most_common(8),
    }

pref = Counter(c.get('preferred_theme') for c in compares)
n_new, n_old = pref.get('new', 0), pref.get('old', 0)
n = n_new + n_old
if n:
    p = sum(math.comb(n, k) for k in range(max(n_new, n_old), n + 1)) / 2**n * 2
    p = min(1.0, p)
else: p = None
agg['preference'] = {'split': dict(pref), 'sign_test_two_sided_p': round(p, 5) if p is not None else None,
                     'note': 'simulation-internal; n=100 personas walking captured evidence, not a live A/B'}

# per-intent preference
prefint = defaultdict(Counter)
for c in compares:
    prefint[intent(c['persona_id'])][c.get('preferred_theme')] += 1
agg['preference']['by_intent'] = {k: dict(v) for k, v in prefint.items()}
prefdev = defaultdict(Counter)
for c in compares:
    prefdev[device(c['persona_id'])][c.get('preferred_theme')] += 1
agg['preference']['by_device'] = {k: dict(v) for k, v in prefdev.items()}

json.dump(agg, open(f'{ROOT}/data/aggregate.json', 'w'), indent=1)
print(json.dumps(agg['preference'], indent=1))
for t in ('old', 'new'):
    print('\n=== ', t.upper(), json.dumps(agg['by_theme'][t]['overall'], indent=1))
    print('identity:', json.dumps({k: v for k, v in agg['identity'][t].items() if k in ('feels_like', 'price_guess', 'top5_concentration', 'distinct_recall_words')}, indent=1))
    print('top recall words:', agg['identity'][t]['recall_words_top15'][:10])
