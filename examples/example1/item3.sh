#!/usr/bin/env bash

set -eu

case "${1:-}" in
    "get_text")
        # This item accepts a parameter.
        echo "notification :: System :: Info :: :: $(date)"
        ;;
    "execute")
        # This item is a notification, does not execute.
        echo "this never executes"
        ;;
esac
