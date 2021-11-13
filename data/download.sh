#!/usr/bin/env bash

# "SLPBUSD"

COINS=("ADABUSD" "ATOMBUSD" "AXSBUSD" "BNBBUSD" "BTCBUSD" "DOGEBUSD" "DOTBUSD" "ETHBUSD" "LTCBUSD" "LUNABUSD" "SOLBUSD" "UNIBUSD" "XMRBUSD" "XRPBUSD")

if [[ ! -d ./zip ]]; then
    mkdir ./zip
fi

if [[ ! -d ./csv ]]; then
    mkdir ./csv
fi

for coin in "${COINS[@]}"; do
    url="${coin}/1m/${coin}-1m-2021-10.zip"
    if ! wget -P ./zip "https://data.binance.vision/data/spot/monthly/klines/${url}"; then
        echo "ERROR: '${coin}' not found"
        exit 2
    fi
    unzip -d ./csv "${coin}-1m-2021-10.zip"
done

exit 0
