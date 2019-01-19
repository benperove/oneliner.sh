#!/bin/sh
git checkout -b upvotes
git add oneliners/ && \
git commit -m 'upvotes counted' && \
git push --set-upstream origin upvotes
