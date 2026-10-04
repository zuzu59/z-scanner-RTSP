#!/usr/bin/env python3
"""Find IPv4 hosts accepting RTSP connections on TCP port 554."""

import argparse
import ipaddress
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

PORT = 554
DEFAULT_PREFIX = 24
DEFAULT_TIMEOUT = 0.5
DEFAULT_WORKERS = 128


def parse_target(value: str) -> ipaddress.IPv4Network:
    try:
        if "/" in value:
            network = ipaddress.ip_network(value, strict=False)
        else:
            # The documented shorthand is an address inside a /24 LAN.
            network = ipaddress.ip_network(f"{value}/{DEFAULT_PREFIX}", strict=False)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not isinstance(network, ipaddress.IPv4Network):
        raise argparse.ArgumentTypeError("Seuls les réseaux IPv4 sont pris en charge.")
    return network


def probe_host(address: str, timeout: float, ping_path: str | None) -> tuple[bool, bool]:
    """Return (host responds to ping or RTSP, RTSP port is open)."""
    ping_alive = False
    if ping_path:
        try:
            result = subprocess.run(
                [ping_path, "-n", "-c", "1", "-W", str(max(1, int(timeout + 0.999))), address],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout + 1,
                check=False,
            )
            ping_alive = result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass

    try:
        with socket.create_connection((address, PORT), timeout=timeout):
            return True, True
    except (OSError, TimeoutError):
        return ping_alive, False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recherche les hôtes ayant le port TCP 554 (RTSP) ouvert."
    )
    parser.add_argument(
        "target", type=parse_target,
        help="adresse IPv4 (interprétée en /24) ou réseau CIDR, ex. 192.168.0.1 ou 192.168.0.0/24",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"délai de connexion par hôte en secondes (défaut : {DEFAULT_TIMEOUT})")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"nombre maximal de connexions simultanées (défaut : {DEFAULT_WORKERS})")
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout doit être supérieur à 0")
    if args.workers < 1:
        parser.error("--workers doit être supérieur ou égal à 1")

    network = args.target
    hosts = list(network.hosts())
    print(f"Scan de {network} : {len(hosts)} adresses, TCP/{PORT}", flush=True)
    started = time.monotonic()
    found = []
    active = []
    scanned = 0
    ping_path = shutil.which("ping")
    if not ping_path:
        print("Avertissement : ping introuvable, seuls les hôtes ouverts sur TCP/554 seront détectés comme actifs.", file=sys.stderr)
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            jobs = {executor.submit(probe_host, str(host), args.timeout, ping_path): str(host) for host in hosts}
            for job in as_completed(jobs):
                scanned += 1
                address = jobs[job]
                is_active, rtsp_open = job.result()
                if is_active:
                    active.append(address)
                if rtsp_open:
                    found.append(address)
                    print(f"[OUVERT] {address}:{PORT}", flush=True)
    except KeyboardInterrupt:
        print("Scan interrompu.", file=sys.stderr)
        return 130

    elapsed = time.monotonic() - started
    print(f"\nAdresses IP actives : {len(active)}.")
    print(f"Adresses scannées : {scanned}/{len(hosts)}.")
    if found:
        print(f"{len(found)} hôte(s) avec TCP/{PORT} ouvert ({elapsed:.1f} s).")
    else:
        print(f"Aucun port TCP/{PORT} ouvert détecté ({elapsed:.1f} s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
