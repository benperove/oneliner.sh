# oneliner.sh - be a CLI samurai

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Build Status](https://travis-ci.com/benperove/oneliner.sh.svg?token=GZU4bGtHVss1DmX96oD4&branch=master)](https://travis-ci.com/benperove/oneliner.sh) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/benperove/oneliner.sh.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/benperove/oneliner.sh/context:python)

oneliner.sh is a currated collection of the best oneliner commands for linux.

* 100% CLI-based + extremely fast
* upvote your favorite commands
* share commands from your toolbox

Basic usage:

curl oneliner.sh/command+name

Examples

```
curl oneliner.sh/kubectl
```

```
curl oneliner.sh/docker-compose/install
```

1. login

curl oneliner.sh/login

copy the link, paste it into a browser & authorize oneliner.sh with your github account.

once authorized, then you can copy the text in the box and paste it back into your terminal.

you will be logged in.

2. to add a new command

for example, let's say you wanted to add a command for finding and replacing a string of text within multiple files.

you could type:

```
cat <<EOF | curl -b ~/.oneliner.sh.cookie.txt --data-binary @- oneliner.sh/linux/find+files+search+replace/add
find ./ -type f -print0 | xargs -0 sed -i 's/1.2.3.4/1.2.3.5/g'
EOF
```
linux/find+files+search+replace added to the queue by benperove
