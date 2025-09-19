Handling exposed Google Cloud service account keys

1) Immediately rotate keys
   - In Google Cloud Console go to IAM & Admin → Service Accounts → select the service account → Keys → Delete the compromised key.
   - Create a new key only if necessary and download it securely.

2) Do not commit keys
   - Add `service_account.json` and `.streamlit/secrets.toml` to `.gitignore`.
   - Use `service_account.json.example` as a template in the repo.

3) Use hosted secrets
   - For Streamlit Cloud, add the full JSON into the app's Settings → Secrets as `GCP_SERVICE_ACCOUNT`.
   - For CI/CD, store the JSON in your CI provider's secrets and write to a file at runtime.

4) Prevent future leaks
   - Install `pre-commit` and run `pre-commit install` locally.
   - Consider enabling automated secret scanning on GitHub.
