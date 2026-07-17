#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Compile Typst file to PDF")
    parser.add_argument("input_file", help="Path to the input .typ file")
    parser.add_argument("-o", "--output", help="Path to the output .pdf file", default=None)
    parser.add_argument("--watch", action="store_true", help="Watch for changes and recompile")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors (exit non-zero if stderr contains 'warning:')")

    args = parser.parse_args()

    input_path = os.path.abspath(args.input_file)
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = os.path.splitext(input_path)[0] + ".pdf"

    cmd = ["typst", "watch" if args.watch else "compile", input_path, output_path]

    print(f"Running: {' '.join(cmd)}")
    try:
        if args.watch:
            subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            diagnostics = result.stderr.strip()

            # Always print diagnostics (errors AND warnings) so they are never hidden
            if diagnostics:
                print(diagnostics, file=sys.stderr)

            has_warning = "warning:" in diagnostics.lower()

            if result.returncode != 0:
                print(f"❌ Compilation failed with error code {result.returncode}")
                sys.exit(result.returncode)

            if args.strict and has_warning:
                print("❌ Strict build failed: Typst emitted warnings (see above).",
                      file=sys.stderr)
                sys.exit(2)

            # Success — print summary
            print(f"✅ Successfully compiled to {output_path}")
            if os.path.exists(output_path):
                size_kb = os.path.getsize(output_path) / 1024
                print(f"   File size: {size_kb:.1f} KB")

    except FileNotFoundError:
        print("Error: 'typst' command not found.")
        print("Typst may be pre-installed; first verify with: typst --version")
        print("If truly missing, install with: sudo apt-get install -y xz-utils && "
              "cd /tmp && wget -q https://github.com/typst/typst/releases/latest/download/"
              "typst-x86_64-unknown-linux-musl.tar.xz && "
              "tar -xf typst-x86_64-unknown-linux-musl.tar.xz && "
              "sudo mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/")
        sys.exit(1)


if __name__ == "__main__":
    main()
