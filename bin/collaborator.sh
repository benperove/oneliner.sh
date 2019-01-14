#!/bin/sh
ACCESS_TOKEN=$(git config auth.token)
COLLAB_USERNAME="benperove"
curl -i -H "Authorization: token $ACCESS_TOKEN" -X PUT -d '' "https://api.github.com/repos/benperove/oneliner.sh/collaborators/$COLLAB_USERNAME"
