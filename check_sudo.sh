#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Please enter as root"
  exit
fi
