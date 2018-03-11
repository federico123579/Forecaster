#!/bin/bash
read -p "Telegram token: " telegram_token
read -p "Sentry token: " sentry_token
export FORECASTER_TELEGRAM_TOKEN=telegram_token
export FORECASTER_SENTRY_TOKEN=sentry_token
echo tokens saved
