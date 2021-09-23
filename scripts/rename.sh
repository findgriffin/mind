#! /bin/sh

if [[ $# -eq 0 ]] ; then
        echo 'New name required'
            exit 0
fi

echo "Renaming stub to $1"

git mv stub $1
git mv $1/stub.py $1/$1.py 
git mv tests/test_stub.py tests/test_$1.py

sed -i '' -e "s/stub/$1/g" run.py 
sed -i '' -e "s/stub/$1/g" tests/test_$1.py
sed -i '' -e "s/stub/$1/g" Makefile
git add run.py tests/test_$1.py Makefile

make
git commit -m "Renamed stub -> $1"
