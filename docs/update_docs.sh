#!/bin/sh

git add -A . &&
git commit -m "Updated documentation"

make html &&
git stash &&
git checkout gh-pages &&
git rm -r :/ &&
git reset -- :/CNAME :/.nojekyll && git checkout -- :/CNAME :/.nojekyll &&
mv ./_build/html/* ../. &&
git add -A :/ &&
git reset -- :/docs &&
git commit -m "Updated documentation" &&
git push origin gh-pages &&
git checkout master &&
git stash pop --index
