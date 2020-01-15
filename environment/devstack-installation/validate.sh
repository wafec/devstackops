#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Root required"
  exit
fi
