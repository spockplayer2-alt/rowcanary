"""Run from the repository root after installing RowCanary: python -m examples.integration."""

from pathlib import Path
from tempfile import TemporaryDirectory

from rowcanary import check_file, load_config, write_probes


def main():
    config = load_config(Path(__file__).with_name("config.json"))
    with TemporaryDirectory(prefix="rowcanary-example-") as directory:
        sample = Path(directory) / "controls.json"
        write_probes(sample, **config.make_options())
        report = check_file(sample, **config.check_options())
        print(f"{'PASS' if report.ok else 'FAIL'}: {report.passed}/{report.total}")
        return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
