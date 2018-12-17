#!/bin/sh
#automatically merge contrib commits into master

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
LAST_COMMIT=$(git rev-list -1 HEAD)

echo Automatically merging commit $LAST_COMMIT from $CURRENT_BRANCH rippling to master

case $CURRENT_BRANCH in
contrib)
  git checkout master && git merge contrib
  git checkout $CURRENT_BRANCH
  ;;
esac
