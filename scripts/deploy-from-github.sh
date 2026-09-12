#!/usr/bin/env bash
set -euo pipefail

expected_sha="${1:?Expected 40-character Git commit SHA is required}"
if [[ ! "$expected_sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Invalid commit SHA: $expected_sha" >&2
  exit 2
fi

repo="/srv/raspi-data/repos/VmManager"
runtime="/srv/raspi-data/vmmanager"
app="$runtime/app"
venv="$runtime/venv"
service="vmmanager.service"
lock="/run/lock/vmmanager-deploy.lock"

exec 9>"$lock"
flock -n 9 || {
  echo "Another VM Manager deployment is already running." >&2
  exit 1
}

test -d "$repo/.git"
git_as_loxberry() {
  runuser -u loxberry -- git -C "$repo" "$@"
}
test -f "$repo/vm_webapp/app/requirements.txt"
test -f /etc/vmmanager/vmmanager.env

git_as_loxberry fetch --quiet origin main
remote_sha="$(git_as_loxberry rev-parse origin/main)"
if [[ "$expected_sha" != "$remote_sha" ]]; then
  echo "Refusing deployment: expected $expected_sha, origin/main is $remote_sha" >&2
  exit 1
fi

previous_sha="$(git_as_loxberry rev-parse HEAD)"
rollback() {
  status=$?
  if [[ $status -ne 0 ]]; then
    echo "Deployment failed; restoring source revision $previous_sha." >&2
    git_as_loxberry reset --hard --quiet "$previous_sha" || true
  fi
  exit $status
}
trap rollback EXIT

echo "Deploying VM Manager commit $expected_sha"
git_as_loxberry reset --hard --quiet "$expected_sha"

install -d -o vmmanager -g vmmanager -m 0750 "$runtime" "$runtime/home" "$app"
rsync -a --delete \
  --exclude '.git' \
  --exclude '.github' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'my_venv' \
  --exclude 'current.log' \
  "$repo/vm_webapp/" "$app/"
chown -R vmmanager:vmmanager "$app"

if [[ ! -x "$venv/bin/python" ]]; then
  runuser -u vmmanager -- python3 -m venv "$venv"
fi
runuser -u vmmanager -- "$venv/bin/pip" install --disable-pip-version-check -r "$app/app/requirements.txt"

install -o root -g root -m 0644 \
  "$repo/deploy/systemd/vmmanager.service" \
  /etc/systemd/system/vmmanager.service

systemctl daemon-reload
systemctl restart "$service"
systemctl is-active --quiet "$service"

ready=0
for _ in {1..15}; do
  if curl --fail --silent --show-error --max-time 2 http://127.0.0.1:8000/healthz >/dev/null; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "$ready" -ne 1 ]]; then
  echo "VM Manager did not become ready on port 8000 within 15 seconds." >&2
  exit 1
fi

# The readiness endpoint only proves that Uvicorn listens. Verify that the
# rendered web UI works as well, including its Jinja template.
curl --fail --silent --show-error --max-time 15 http://127.0.0.1:8000/ >/dev/null

trap - EXIT
echo "VM Manager deployment completed: $expected_sha"
