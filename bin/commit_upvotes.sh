#!/bin/sh
git config --global user.email "benperove@gmail.com"
git config --global user.name "Benjamin Perove"
git add oneliners/ && git commit -m 'upvotes counted' && git push
