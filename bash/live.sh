#!/bin/bash

echo -e "123\n123" | sudo passwd stack
export EXT_HOST=$HOST
su --preserve-environment -c$(pwd)/live_root.sh root