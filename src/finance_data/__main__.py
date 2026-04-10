"""Entry point: python -m finance_data [verify] [--json] [--smoke] [--dashboard]"""
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m finance_data",
        description="FinanceData — verify system integrity",
    )
    parser.add_argument(
        "command", nargs="?", default="verify", choices=["verify"],
        help="Command to run (default: verify)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests (requires network)")
    parser.add_argument("--dashboard", action="store_true", help="Include dashboard API check")
    args = parser.parse_args()

    from finance_data.verify import print_report, run_verify

    report = run_verify(include_smoke=args.smoke, include_dashboard=args.dashboard)
    print_report(report, as_json=args.json)
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
