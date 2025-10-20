#!/bin/bash
cd "$(dirname "$0")"
echo "Running run_school..."
wine "run_school" || ./"run_school" "$@"
