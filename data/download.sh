#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
BASE_URL="https://data.binance.vision/data/spot/monthly/klines"
zip_dir="${SCRIPT_DIR}/zip"
csv_dir="${SCRIPT_DIR}/csv/history"

# "SLPBUSD"
COINS=("ADABTC" "ADABUSD" "ADAETH" "ATOMBUSD" "AXSBUSD" "BNBBTC" "BNBBUSD" "BNBETH" "BNBUSDT" "BTCBUSD" "BTCUSDT" "DOGEBUSD" "DOGEUSDT" "DOTBUSD" "ETHBTC" "ETHBUSD" "ETHUSDT" "LTCBNB" "LTCBTC" "LTCBUSD" "LTCUSDT" "LUNABUSD" "SOLBNB" "SOLBUSD" "UNIBUSD" "XMRBNB" "XMRBTC" "XMRBUSD" "XMRUSDT" "XRPBUSD")

if [[ ! -d ${zip_dir} ]]; then
    mkdir "${zip_dir}"
fi

if [[ ! -d ${csv_dir} ]]; then
    mkdir -p "${csv_dir}"
fi

for pair in "${COINS[@]}"; do
    for i in {3..12}; do
        if [[ ${i} -lt 10 ]]; then
            month="0${i}"
        else
            month="${i}"
        fi
        url_path="${pair}/1m/${pair}-1m-2021-${month}.zip"
        zip_file="${zip_dir}/${pair}-1m-2021-${month}.zip"
        if [[ ! -f ${zip_file} ]]; then
            echo
            echo
            echo "Downloading ${zip_file}"
            echo
            if ! wget -P "${zip_dir}" "${BASE_URL}/${url_path}"; then
                exit 2
            fi
            if ! unzip -d "${csv_dir}" -n "${zip_file}"; then
                exit 2
            fi
        fi
    done
done

exit 0
