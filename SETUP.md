# Set it up yourself — Azure + Gmail

Reproduce the inbox-triage automation end to end. ~30 min, ~$0 on a normal/Sponsorship
subscription. Everything defaults to **dry-run** — it won't touch your mail until you opt in.

## Prerequisites
- An Azure subscription + `az` CLI (`az login`)
- Azure Functions Core Tools v4 (`brew install azure-functions-core-tools@4`)
- Python 3.11
- A Google account (for Gmail)

```bash
git clone https://github.com/knightkill/prompt-to-productivity && cd prompt-to-productivity
python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env       # fill in as you go below
```

## 1 · Azure OpenAI (the classifier)
Create (or reuse) an Azure OpenAI resource with a chat deployment, then put its
endpoint/key/deployment into `.env` (`AZURE_OPENAI_*`). A small/cheap model is plenty.

> gpt-5 family: the code uses `max_completion_tokens` and no temperature override.

## 2 · Gmail OAuth (one-time, mints a refresh token)
1. Google Cloud Console → enable the **Gmail API**.
2. OAuth consent screen → **External**, add your address as a **Test user**.
3. Credentials → **OAuth client ID → Desktop app** → download as `credentials.json` (repo root).
4. Mint the token (opens a browser; grant `gmail.readonly` + `gmail.modify`):
   ```bash
   python -c "from src.gmail.client import authenticate_gmail; authenticate_gmail()"
   # writes token.json — the refresh token the cloud function will reuse headless
   ```

## 3 · Try it locally (no Azure deploy needed)
```bash
python scripts/run_local.py --samples                       # classify sample emails
python scripts/run_local.py --query "in:inbox is:unread" --limit 5   # dry-run over real inbox
python scripts/run_local.py --apply --live --limit 5        # actually label/archive (guarded)
```
Edit `policy.md` and re-run — behaviour changes with no code change.

## 4 · Provision Azure (one-time)
```bash
RG=rg-prompt2productivity; LOC=eastus2
STORAGE=p2ptriage$RANDOM; FUNCAPP=p2p-triage-$RANDOM; KV=p2pkv$RANDOM

az provider register --namespace Microsoft.Web --wait     # Sponsorship subs need this
az group create -n $RG -l $LOC
az storage account create -n $STORAGE -g $RG -l $LOC --sku Standard_LRS
az functionapp create -n $FUNCAPP -g $RG -s $STORAGE --consumption-plan-location $LOC \
  --runtime python --runtime-version 3.11 --functions-version 4 --os-type Linux
az functionapp identity assign -n $FUNCAPP -g $RG          # managed identity
az keyvault create -n $KV -g $RG -l $LOC --enable-rbac-authorization true

# grant the function's identity read access, and yourself write access
KVID=$(az keyvault show -n $KV --query id -o tsv)
PRINCIPAL=$(az functionapp identity show -n $FUNCAPP -g $RG --query principalId -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" --scope $KVID
az role assignment create --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Key Vault Secrets Officer" --scope $KVID
sleep 30   # RBAC propagation

# secrets → Key Vault (from your local .env / token.json)
az keyvault secret set --vault-name $KV -n azure-openai-key --value "$(grep -E '^AZURE_OPENAI_KEY=' .env | sed -E 's/.*=//; s/\"//g')"
az keyvault secret set --vault-name $KV -n storage-connection-string --value "$(az storage account show-connection-string -n $STORAGE -g $RG --query connectionString -o tsv)"
az keyvault secret set --vault-name $KV -n gmail-token-json --file token.json

# non-secret config + Key Vault pointer (dry-run ON for safety)
az functionapp config appsettings set -n $FUNCAPP -g $RG --settings \
  AZURE_OPENAI_ENDPOINT="$(grep -E '^AZURE_OPENAI_ENDPOINT=' .env | sed -E 's/.*=//; s/\"//g')" \
  AZURE_OPENAI_DEPLOYMENT_NAME="<your-deployment>" AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
  KEY_VAULT_URI="https://$KV.vault.azure.net/" TRIAGE_STATE_CONTAINER="triage-state" \
  TRIAGE_LIMIT="2" TRIAGE_DRY_RUN="true" AzureWebJobsFeatureFlags="EnableWorkerIndexing"
echo "FUNCAPP=$FUNCAPP"   # note this for deploy
```

## 5 · Deploy + run
```bash
func azure functionapp publish $FUNCAPP --python --build remote   # zip won't remote-build on Linux Consumption

# manual run (dry-run): grab the key from the publish output or:
KEY=$(az functionapp keys list -g $RG -n $FUNCAPP --query functionKeys.default -o tsv)
curl "https://$FUNCAPP.azurewebsites.net/api/triage?limit=5&code=$KEY"

# go live (the 10-min timer starts actually labeling/archiving):
az functionapp config appsettings set -n $FUNCAPP -g $RG --settings TRIAGE_DRY_RUN=false
```

## Controls & cleanup
```bash
# pause mutations / stop the timer
az functionapp config appsettings set -n $FUNCAPP -g $RG --settings TRIAGE_DRY_RUN=true
az functionapp config appsettings set -n $FUNCAPP -g $RG --settings "AzureWebJobs.handle_scheduled_triage.Disabled=true"
# tear everything down
az group delete -n $RG --yes
```

**Safety:** dry-run default · never-touch allowlist (starred/VIP/your threads) · idempotent (Blob) · every decision in an audit log (undo = re-add the `INBOX` label).
