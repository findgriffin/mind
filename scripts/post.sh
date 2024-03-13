#! /bin/sh

URL=`envchain findgriffin aws --region=us-west-2 lambda get-function-url-config --function-name mind-prod | jq -r '.FunctionUrl'`

curl -v -X POST "$URL" \
      -H 'X-Forwarded-Proto: https' \
      -H 'content-type: application/json' \
      -d '{ "example": "test" }'
