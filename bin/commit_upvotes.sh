#!/bin/sh
git checkout -b upvotes
git pull --no-edit
git add oneliners/
git commit -m 'upvotes counted'
git push --set-upstream origin upvotes
