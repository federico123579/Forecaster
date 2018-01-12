#!/bin/sh
read -p "What version do you want to release?: " version
cd $(dirname $(dirname ${BASH_SOURCE[0]}))  # go to source
git tag $version
git push --tag
git push
