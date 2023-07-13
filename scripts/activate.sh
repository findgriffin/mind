#! /bin/sh
STATUS='unknown'


until [ $STATUS == '"Active"' ]
do
  STATUS=`envchain findgriffin aws --region=us-west-2 lambda get-function --function-name mind-prod | jq '.Configuration.State'`
  echo "Status: $STATUS"
done

