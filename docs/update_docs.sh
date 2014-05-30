#!/bin/sh

git add -A . &&
git commit -m "Updated documentation"

make html &&
git checkout gh-pages &&
git rm -r :/ &&
git reset -- :/CNAME :/.nojekyll && git checkout -- :/CNAME :/.nojekyll &&
mv ./_build/html/* ../. &&
git add -A :/ &&
git reset -- :/docs &&
git commit -m "Updated documentation" &&
git checkout master
