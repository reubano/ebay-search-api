#!/bin/sh
#
# A script to disallow syntax errors to be committed
# by running a checker (lint, pep8, pylint...)  on them
#

# Redirect output to stderr.
exec 2>&1

# necessary check for initial commit
git rev-parse --verify HEAD > /dev/null
if [ $? == 0 ]; then
	against=HEAD
else
	# Initial commit: diff against an empty tree object
	against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# set Internal Field Separator to newline (dash does not support $'\n')
IFS='
'

# get a list of staged files
for LINE in $(git diff-index --cached --full-index $against); do
	SHA=$(echo $LINE | cut -d' ' -f4)
	STATUS=$(echo $LINE | cut -d' ' -f5 | cut -d'	' -f1)
	FILENAME=$(echo $LINE | cut -d' ' -f5 | cut -d'	' -f2)
	FILEEXT=$(echo $FILENAME | sed 's/^.*\.//')

	# do not check deleted files
	if [ $STATUS == "D" ]; then
		continue
	fi

	# only check files with proper extension
	if [ $FILEEXT == 'php' ]; then
		COMMAND='php -l'
	elif [ $FILEEXT == 'py' ]; then
		COMMAND='python manage.py lint --file'
	else
		continue
	fi

	git cat-file -p $SHA > tmp.txt
	RESULT=$(eval "$COMMAND tmp.txt"); PASSED=$?

	if [ $PASSED != 0 ]; then
		echo "Check failed on $FILENAME"
		for LINE in $RESULT; do echo $LINE; done
  else
		echo "Found no errors in $FILENAME!"
	fi
done

unset IFS
if [ -f tmp.txt ]; then
  rm tmp.txt
fi

exit $PASSED

# If there are whitespace errors, print the offending file names and fail.
# exec git diff-index --check --cached $against --
