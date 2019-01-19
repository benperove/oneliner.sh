#!/bin/sh
#git checkout -b upvotes
git pull origin upvotes --no-edit
git branch --set-upstream-to=origin/upvotes
git add oneliners/
git commit -m 'upvotes counted'
git push --set-upstream origin upvotes
