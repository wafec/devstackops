#!/bin/bash


MYVAR=$(ssh-keyscan -H compute1)
echo "---"
echo $MYVAR