#!/usr/bin/env python3
from pathlib import Path


def metrics(path):
    text = Path(path).read_text()
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return {"lines": len(lines), "bytes": len(text.encode())}


def main():
    human = metrics("examples/garage.human")
    python = metrics("benchmarks/garage_python.py")
    print("Garage CRM source comparison")
    print(f"Human : {human['lines']} non-empty lines, {human['bytes']} bytes")
    print(f"Python: {python['lines']} non-empty lines, {python['bytes']} bytes")
    print(f"Line ratio: {human['lines'] / python['lines']:.2f}x")
    print(f"Byte ratio: {human['bytes'] / python['bytes']:.2f}x")
    print("\nThese measure source surface area only, not developer time, model tokens, or energy.")


if __name__ == "__main__":
    main()
