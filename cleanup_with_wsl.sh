#!/usr/bin/env bash
set -euo pipefail

workspace="/mnt/c/VinAI/Day16-Track2-Assignment"
terraform_zip="/tmp/day16-terraform-cleanup.zip"
terraform_dir="/tmp/day16-terraform-cleanup-bin"
terraform_bin="${terraform_dir}/terraform"

rm -f "${terraform_zip}"
rm -rf "${terraform_dir}"
mkdir -p "${terraform_dir}"

curl --fail --silent --show-error --location \
  --output "${terraform_zip}" \
  "https://releases.hashicorp.com/terraform/1.16.4/terraform_1.16.4_linux_amd64.zip"
python3 -m zipfile -e "${terraform_zip}" "${terraform_dir}"
chmod 755 "${terraform_bin}"

export AWS_SHARED_CREDENTIALS_FILE="/mnt/c/Users/Htungf/.aws/credentials"
export AWS_CONFIG_FILE="/mnt/c/Users/Htungf/.aws/config"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_SDK_UA_APP_ID="AWSSkill-Compute"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy

cd "${workspace}/terraform"
"${terraform_bin}" init -input=false
"${terraform_bin}" destroy -auto-approve 2>&1 \
  | tee "${workspace}/evidence/terraform_destroy.txt"
