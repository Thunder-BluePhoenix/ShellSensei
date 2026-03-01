#!/usr/bin/env bash
set -euo pipefail
# ShellSensei wrapper for ss_cargo_2
cargo check -p orionis-engine 2>&1 | Select-String -Pattern "error" -Context 2,2
