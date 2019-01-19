#!/bin/sh
git checkout -b upvotes
git branch --set-upstream-to=origin/upvotes
git pull origin upvotes --no-edit
git add oneliners/
git commit -m 'upvotes counted'
#git push --set-upstream origin upvotes
git push
