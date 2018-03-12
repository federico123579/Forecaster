#!/bin/bash
read -p "Telegram token: " telegram_token
read -p "Sentry token: " sentry_token
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
token_file="$DIR/forecaster/data/tokens.yml"
touch $token_file
echo "telegram: $telegram_token" > $token_file
echo "sentry: $sentry_token" >> $token_file
echo tokens saved
