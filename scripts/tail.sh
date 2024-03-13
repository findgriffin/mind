#! /bin/sh
PREFIX="envchain findgriffin aws --region=us-west-2"
LOG_GROUP="/aws/lambda/mind-prod"

STREAM=`$PREFIX logs describe-log-streams --log-group-name $LOG_GROUP | jq -r '.logStreams | .[0] | .logStreamName'`

echo "Getting events for $STREAM"

$PREFIX logs get-log-events --log-group-name $LOG_GROUP --log-stream-name "$(STREAM)"
