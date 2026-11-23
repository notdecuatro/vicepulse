"""One idempotent production cycle; shared daily slots across campaigns."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path

import vice


def credential_setup():
    path = vice.ROOT / 'credentials.json'
    if path.exists():
        if path.stat().st_mode & 0o077:
            raise ValueError('credentials.json requiere permisos 0600.')
        for key, value in json.loads(path.read_text()).items():
            if key in ('BUFFER_API_KEY', 'CLOUDINARY_URL') and value:
                os.environ[key] = value


def inspect_campaign(path, day):
    config = json.loads(path.read_text())
    blockers = []
    checks = {
        'verified_today': config.get('verified_on') == day,
        'joined': config.get('joined') is True,
        'accepting_clips': config.get('accepting_clips') is True,
        'budget_available': config.get('remaining_budget', 0) > 0,
        'creator_eligible': config.get('creator_eligible') is True,
        'full_brief_read': config.get('content_requirements_verified') is True,
        'submission_ready': config.get('submission_session_ready') is True,
        'preapproval_resolved': config.get('preapproval_required') is False,
        'source_configured': bool(config.get('sources')),
    }
    blockers.extend(key for key, passed in checks.items() if not passed)
    if checks['source_configured']:
        try:
            vice.approved_sources(config, allow_download=False)
        except (ValueError, KeyError, OSError, TypeError):
            blockers.append('source_authorized_and_available')
    return config, blockers


def run_cycle(db, day, mode='plan', *, config_paths=None, producer=None, dispatcher=None):
    paths = config_paths or sorted((vice.ROOT / 'campaigns').glob('*.json'))
    producer = producer or vice.produce
    dispatcher = dispatcher or vice.dispatch
    campaigns, report = [], {'day': day, 'mode': mode, 'campaigns': [], 'slots': [], 'errors': []}
    seen, names = set(), {}
    for path in paths:
        try:
            config, blockers = inspect_campaign(path, day)
            url = config['campaign_url']
            if url in seen:
                raise ValueError('Campaña duplicada en configuración.')
            seen.add(url)
            names[url] = path.stem
            report['campaigns'].append({'config': str(path.relative_to(vice.ROOT)),
                                        'campaign': url, 'blockers': blockers})
            if not blockers:
                campaigns.append(config)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            report['errors'].append({'config': path.name, 'error': str(exc)})
    strategy_path = vice.ROOT / 'strategy.json'
    strategy = json.loads(strategy_path.read_text()) if strategy_path.exists() else {}
    priority = strategy.get('campaign_order', ['dylan', 'bobby', 'cnpl'])
    rank = {name: index for index, name in enumerate(priority)}
    campaigns.sort(key=lambda c: rank.get(names[c['campaign_url']], 999))
    campaigns = campaigns[:min(2, max(0, strategy.get('max_active_campaigns', 2)))]
    claimed = set()
    recovery = vice.ROOT / 'recovery-state.json'
    if recovery.exists():
        claimed.update(json.loads(recovery.read_text()).get('claimed_slots', {}).get(day, []))
    rows = {row['slot']: row for row in db.execute('SELECT * FROM clips WHERE day=?', (day,))}
    if mode != 'plan':
        missing = [key for key in ('BUFFER_API_KEY', 'CLOUDINARY_URL') if not os.getenv(key)]
        if missing:
            report['errors'].append({'stage': 'credentials', 'missing': missing})
            return report
    for slot in (1, 2):
        existing = rows.get(slot)
        if existing and mode == 'plan':
            campaign = next((c for c in report['campaigns'] if c['campaign'] == existing['campaign']), None)
            jobs = [dict(job) for job in db.execute(
                'SELECT network,status,post_id,public_url,reward_ref FROM jobs WHERE day=? AND slot=?',
                (day, slot))]
            report['slots'].append({'slot': slot, 'status': 'existing',
                                    'campaign': existing['campaign'], 'jobs': jobs,
                                    'delivery_blockers': campaign['blockers'] if campaign else ['campaign_not_configured']})
            continue
        if slot in claimed and not existing:
            report['slots'].append({'slot': slot, 'status': 'reconciliation_required'})
            continue
        choices = [c for c in campaigns if not existing or c['campaign_url'] == existing['campaign']]
        if not existing and len(choices) > 1:
            offset = (slot - 1) % len(choices)
            choices = choices[offset:] + choices[:offset]
        if not choices:
            report['slots'].append({'slot': slot, 'status': 'blocked',
                                    'reason': 'No hay campaña verificada y admisible con fuente.'})
            continue
        if mode == 'plan':
            report['slots'].append({'slot': slot, 'status': 'existing' if existing else 'planned',
                                    'campaign': choices[0]['campaign_url']})
            continue
        for config in choices:
            try:
                producer(db, config, day, slot=slot)
                row = db.execute('SELECT * FROM clips WHERE day=? AND slot=?', (day, slot)).fetchone()
                if row is None:
                    raise ValueError('No se registró la exportación.')
                from quality import require_export
                require_export(Path(row['file']))
                if mode == 'publish':
                    review_path = Path(row['file']).with_suffix('.review.json')
                    review = json.loads(review_path.read_text()) if review_path.exists() else {}
                    if review.get('sha256') != row['hash'] or review.get('approved') is not True:
                        raise ValueError('Falta revisión editorial aprobada para este archivo exacto.')
                dispatcher(db, config, day, slot, mode != 'publish')
                report['slots'].append({'slot': slot, 'campaign': config['campaign_url'], 'status': mode})
                break
            except Exception as exc:
                # Production may have committed a clip before a remote timeout. Never switch it.
                committed = db.execute('SELECT 1 FROM clips WHERE day=? AND slot=?', (day, slot)).fetchone()
                message = str(exc)
                for key in ('BUFFER_API_KEY', 'CLOUDINARY_URL'):
                    value = os.getenv(key)
                    if value:
                        message = message.replace(value, '[redacted]')
                report['errors'].append({'slot': slot, 'campaign': config['campaign_url'],
                                         'error': type(exc).__name__ + ': ' + message[:1000]})
                if committed:
                    break
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['plan', 'draft', 'publish'], nargs='?', default='plan')
    args = parser.parse_args()
    day = dt.datetime.now(vice.TZ).date().isoformat()
    credential_setup()
    with vice.db_file() as db, open(vice.STATE / 'worker.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        report = run_cycle(db, day, args.mode)
        vice.atomic_json(vice.STATE / 'worker-last-run.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report['errors'] or any(item['status'] in ('blocked', 'reconciliation_required') for item in report['slots']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
