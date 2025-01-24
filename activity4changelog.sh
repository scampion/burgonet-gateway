#!/bin/bash
# Script: last_24h_git_activity_post_for_twitter.sh
# Description: Extracts Git diff and commit messages from the last 24 hours, sends it to Deepseek for a Twitter message, and posts it to X (Twitter).

# File to store Git activity
OUTPUT_FILE="/tmp/activity.git.txt"

# Get the current date and the date 24 hours ago
#CURRENT_DATE=$(date +%Y-%m-%dT%H:%M:%S)
#LAST_24H_DATE=$(date -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)
# Get the current date and the date 24 hours ago (macOS/BSD compatible)
CURRENT_DATE=$(date +%Y-%m-%dT%H:%M:%S)
LAST_24H_DATE=$(date -v -24H +%Y-%m-%dT%H:%M:%S)


# Extract Git commits and diff from the last 24 hours
echo "Git activity in the last 24 hours (since $LAST_24H_DATE):" > "$OUTPUT_FILE"
git log --since="$LAST_24H_DATE" --until="$CURRENT_DATE" --pretty=format:'%h - %an, %ar : %s' >> "$OUTPUT_FILE"
echo -e "\n\nDiffs:\n" >> "$OUTPUT_FILE"
git diff "@{24 hours ago}" -- . ':!www/chart.js' >> "$OUTPUT_FILE"
  
# Send the content to Deepseek for a Twitter message
DEEPSEEK_PROMPT="create a changelog section to explain what happened in this code repository, the message must contain emojis"
# Sanitize the activity content for JSON by escaping special characters
ACTIVITY_CONTENT=$(cat "$OUTPUT_FILE" | \
    tr -d '\000-\031' | \
    jq -sR . | sed 's/^"\(.*\)"$/\1/')

curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
       \"model\": \"deepseek-chat\",
       \"messages\": [
         {\"role\": \"user\", \"content\": \"$DEEPSEEK_PROMPT\n\n$ACTIVITY_CONTENT\"}
       ]
     }"

#
#MESSAGE=$(curl -X POST "https://api.deepseek.com/v1/chat/completions" \
#  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
#  -H "Content-Type: application/json" \
#  -d "{
#       \"model\": \"deepseek-chat\",
#       \"messages\": [
#         {\"role\": \"user\", \"content\": \"$DEEPSEEK_PROMPT\n\n$ACTIVITY_CONTENT\"}
#       ]
#     }" | jq -r '.choices[0].message.content')
#

echo $MESSAGE  | pbcopy





