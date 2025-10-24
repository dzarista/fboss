#!/bin/bash

set -x

TOKEN_RESPONSE=$(curl --location --request POST "https://auth.dev.corp.arista.io/token?scope=openid%20profile%20email%20federated:id%20groups" \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=password" \
  --data-urlencode "username=${SRV_FBOSS_USERNAME}" \
  --data-urlencode "password=${SRV_FBOSS_PASSWORD}" \
  --data-urlencode "client_id=ldap" \
  --data-urlencode "client_secret=")

TOKEN=$(echo "$TOKEN_RESPONSE" | jq .id_token -r)

BUG_TITLE="Upstream changes in ${PR_TITLE} made by ${PR_AUTHOR_LOGIN}"
ASSIGNEE_EMAIL="fbosstest-dev@arista.com"
BUG_DESCRIPTION="Bug automatically filed for merged PR: ${PR_URL}. Please fill out the title and description."

JSON_PAYLOAD=$(jq -n \
  --arg reportedBy "arastra@arista.com" \
  --arg package "FbossTest/-" \
  --arg issueType "BUG" \
  --arg priority "MU (Must understand)" \
  --arg title "$BUG_TITLE" \
  --arg assignee "$ASSIGNEE_EMAIL" \
  --arg status "NEW" \
  --arg description "$BUG_DESCRIPTION" \
  --argjson blocks "[1097486]" \
  '{
    bugs: [
      {
        reportedBy: $reportedBy,
        package: $package,
        issueType: $issueType,
        priority: $priority,
        title: $title,
        assignee: $assignee,
        status: $status,
        resolution: "",
        description: $description,
        blocks: $blocks
      }
    ]
  }')

echo "Sending this JSON payload:"
echo "$JSON_PAYLOAD" | jq .

curl --location --request POST \
  'https://bugs-service.dev.corp.arista.io/v3/bugs' \
  --header "Authorization: Bearer $TOKEN" \
  --header "x-oidc-client-id: ldap" \
  --header "Content-Type: application/json" \
  --data-raw "$JSON_PAYLOAD"

echo "Bug creation request sent."
