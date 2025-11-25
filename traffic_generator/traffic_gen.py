import argparse
import random
import time
import sys
import ipaddress
from datetime import datetime, timedelta
import scapy.all as scapy

DEFAULT_PING_COUNT = 4
MIN_SLEEP_BETWEEN_PINGS = 0.2
DEFAULT_RATE_PER_SEC = 1.0

def parse_destinations(dest_str: str):
    """
    :param dest_str:
    Unterstützt folgende Formen:
    - "192.168.10.11-20"    -> interpretiert als .11 bis .20 (letztes Oktett)
    - "192.168.10.11+20+23" -> .11, .20, .23 (+ letzte Oktette)
    - "192.168.10.11&192.168.170.20" -> zwei vollständige IPs (mit & getrennt)
    todo - "192.168.10.11-13&192.168.170.20+8&192.168.0.5" -> Alles kombiniert ('&', '+' und '-')
    - einzelne IP "10.0.0.5"
    :return: eine list von IP destinations
    """
    parts = dest_str.split('&')
    addresses = []
    for p in parts:
        if '-' in p and '.' in p:
            base, range_ = p.rsplit('.', 1)
            start_str, end_str = range_.split('-', 1)
            start = int(start_str)
            end = int(end_str)
            if not (0 <= start <= 255 and 0 <= end <= 255 and start <= end):
                raise ValueError(f"Ungültiger Bereich: {p}")
            for last in range(start, end+1):
                addresses.append(f"{base}.{last}")
        elif '+' in p and '.' in p:
            base, tail = p.split('.', 3)[:2]
            if p.count('.') < 3:
                print(f"Die IP-Adresse passt nicht: '{dest_str}' hat zu wenige Oktetten")
                sys.exit(0)
            elif p.count('.') > 3:
                print(f"Die IP-Adresse passt nicht: '{dest_str}' hat zu viele Oktetten")
                sys.exit(0)
            base = p.rsplit('.', 1)[0]
            parts_plus = p.rsplit('.', 1)[1].split('+')
            for item in parts_plus:
                addresses.append(f"{base}.{item}")
        else:
            addresses.append(p.strip())
    validated = []
    for a in addresses:
        try:
            ipaddress.ip_address(a)
            validated.append(a)
        except Exception:
            raise ValueError(f"Ungültige IP: {a}")
    return validated

def do_ping(src: str, dst: str, timeout=2, verbose=False):
    """
    Ein einzelner ICMP echo request.
    todo quiet hinzufügen
    :param src:
    :param dst:
    :param timeout:
    :param verbose:
    :return:
    """
    pkt = scapy.IP(dst=dst)
    if src:
        pkt.src = src
    pkt = pkt/scapy.ICMP()
    try:
        reply = scapy.sr1(pkt, timeout=timeout, verbose=False)
        if reply is None:
            if verbose:
                print(f"{dst}: no reply")
            return False
        else:
            if verbose:
                rtt = getattr(reply, 'time', None)
                print(f"{dst}: reply from {reply.src}")
            return True
    except Exception as e:
        if verbose:
            print(f"{dst}: error {e}")
        return False

def schedule_and_send(targets, amount, src, t_at, period, quiet, verbose, coincidental=False, period_is_random=False):
    """
    todo verbose
    :param targets: list of ips
    :param amount: function(target) -> int (how many pings to send for this target)
    :param src:
    :param t_at: either None (now / one-time) or datetime to start
    :param period: function() -> float seconds between cycles, or None for one-time
    :param quiet:
    :param verbose:
    :param coincidental: if True, shuffle the order each cycle
    :param period_is_random:
    :return:
    """
    if t_at:
        now = datetime.now()
        if t_at > now:
            wait = (t_at - now).total_seconds()
            if not quiet:
                print(f"Scheduled start at {t_at.isoformat()} (in {wait:.1f}s)")
            #time.sleep(wait)
    cycle = 0
    while True:
        cycle += 1
        if not quiet:
            print(f"--- Cycle {cycle} start ({datetime.now().isoformat()}) ---")
        order = list(targets)
        if coincidental:
            random.shuffle(order)
        for tgt in order:
            amt = amount(tgt)
            if verbose:
                print(f"{tgt}: will send {amt} pings")
            for i in range(amt):
                ok = do_ping(src, tgt, verbose=verbose)
                if not quiet and verbose:
                    print(f"  [{i+1}/{amt}] -> {'OK' if ok else 'no'}")
                #time.sleep(max(MIN_SLEEP_BETWEEN_PINGS, 1.0/DEFAULT_RATE_PER_SEC))
        if period is None: # todo ändere wenn random period
            break
        next_period = period()
        if next_period is None:
            break
        if not quiet:
            print(f"Next cycle in {next_period:.1f}s")
        time.sleep(next_period)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Argparse Random-Traffic-Gen (sicherer Demo-Prototyp)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-P', '--ping', action='store_true', help='Modus 1: Ein Ziel einmal / mehrfach pingen (single)')
    group.add_argument('-R', '--range-ping', action='store_true', help='Modus 2: Range / mehrere Ziele pingen')

    amount_group = parser.add_mutually_exclusive_group(required=False)
    amount_group.add_argument('-a', '--amount', type=int, default=DEFAULT_PING_COUNT, help=f'Wie oft gepingt wird (default {DEFAULT_PING_COUNT})')
    amount_group.add_argument('-A', '--amount-range', nargs='?', const='RANDOM', help='Min-Max oder leer für random (z.B. "1-4")')

    destination_group = parser.add_mutually_exclusive_group(required=True)
    destination_group.add_argument('-d', '--destination', help='Zieladresse, für -p')
    destination_group.add_argument('-D', '--destinations', help='Destinations string (z.B. 192.168.10.11-20 )')

    parser.add_argument('-s', '--source', help='Source IP')
    parser.add_argument('-t', '--time', nargs='?', const='RANDOM', help='Startzeit HH:MM oder leer -> RANDOM')
    parser.add_argument('-p', '--period', nargs='?', const='RANDOM', help='Perioden in Minuten, oder leer -> RANDOM')
    parser.add_argument('-c', '--coincidental', action='store_true', help='Reihenfolge der Pings zufällig')
    parser.add_argument('-q', '--quiet', action='store_true', help='Wenig Ausgabe')
    parser.add_argument('-v', '--verbose', action='store_true', help='Ausführliche Ausgabe')

    args = parser.parse_args()



    if args.ping:
        if not args.destination:
            parser.error("--ping benötigt --destination")
        if args.A:
            args.amount = args.A
        if args.D:
            parser.error("'-p' hat nur eine destination '-d'")
        if args.coincidental:
            print("coincidental macht bei -p keinen Sinn")
        targets = [args.destination]
    else:
        if not args.destinations:
            parser.error("'--range-ping/-R' benötigt '--destinations/-D'")
        targets = parse_destinations(args.destinations)

    start_time = None
    if args.time:
        if args.time == 'RANDOM':
            delta_sec = random.uniform(1, 3600)
            start_time = datetime.now() + timedelta(seconds=delta_sec)
        else:
            try:
                hh, mm = map(int, args.time.split(':'))
                now = datetime.now()
                start_time = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if start_time < now:
                    start_time += timedelta(days=1)
            except Exception:
                parser.error("Ungültiges Zeitformat für -t. Verwende HH:MM oder gib -t ohne Wert für RANDOM.")
    period = None
    if args.period:
        if args.period == 'RANDOM':
            def period_random():
                return random.uniform(30, 300)
            period = period_random
        else:
            try:
                minutes = float(args.period)
                def period_fixed():
                    return minutes * 60.0
                period = period_fixed
            except Exception:
                parser.error("Ungültiges Format für -p (Period). Gib Minuten als Zahl oder -p ohne Wert für RANDOM.")

    if args.ping:
        def amount_single(target):
            return max(1, args.amount)
    else:
        if args.amount_range is None:
            def amount_range(target):
                return 1
        elif args.amount_range == 'RANDOM':
            def amount_range(target):
                return random.randint(1, DEFAULT_PING_COUNT)
        else:
            if '-' in args.amount_range:
                lo, hi = map(int, args.amount_range.split('-',1))
                def amount_range(target):
                    return random.randint(lo, hi)
            else:
                try:
                    fixed = int(args.amount_range)
                    def amount_range(target):
                        return max(1, fixed)
                except:
                    parser.error("Ungültiger Wert für --amount-range")

        amount_fn = amount_range
    if args.ping:
        amount_fn = amount_single

    try:
        schedule_and_send(
            targets=targets,
            amount=amount_fn,
            src=args.source,
            t_at=start_time,
            period=period,
            quiet=args.quiet,
            verbose=args.verbose,
            coincidental=args.coincidental
        )
    except KeyboardInterrupt:
        print("\nAbgebrochen durch Benutzer.")
        sys.exit(0)

