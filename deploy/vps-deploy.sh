#!/usr/bin/env bash
set -euo pipefail

sha="${1:-}"
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'Expected a 40-character commit SHA' >&2; exit 2; }

repo=/opt/vps-deploy/vmmanager/repo
name=vmmanager-vps
backup=vmmanager-vps-previous
image="local/vmmanager:${sha}"
env_file=/etc/migrated-containers/vmmanager.env
url=http://192.168.178.204:8000

exec 9>/run/lock/vmmanager-vps-deploy.lock
flock -n 9 || { echo 'VMManager deployment already running' >&2; exit 1; }
[[ -f "$env_file" && -d "$repo/.git" ]] || { echo 'Missing VPS environment or repository' >&2; exit 1; }
! docker container inspect "$backup" >/dev/null 2>&1 || { echo 'Previous container still exists; inspect before deploying' >&2; exit 1; }

git -C "$repo" fetch --quiet origin main
[[ "$(git -C "$repo" rev-parse origin/main)" == "$sha" ]] || { echo 'Commit is not current origin/main' >&2; exit 1; }
git -C "$repo" checkout --quiet --detach --force "$sha"
git -C "$repo" clean -fdx -q
docker build --pull -t "$image" -f "$repo/vm_webapp/Dockerfile" "$repo/vm_webapp"

had_previous=false
if docker container inspect "$name" >/dev/null 2>&1; then
  docker stop "$name" >/dev/null
  if ! docker rename "$name" "$backup"; then
    docker start "$name" >/dev/null || true
    echo 'Could not preserve previous VMManager container' >&2
    exit 1
  fi
  had_previous=true
fi

rollback() {
  status=$?
  trap - EXIT
  if (( status != 0 )); then
    docker rm -f "$name" >/dev/null 2>&1 || true
    if "$had_previous"; then
      docker rename "$backup" "$name"
      docker start "$name" >/dev/null
      echo 'Restored previous VMManager container' >&2
    fi
  fi
  exit "$status"
}
trap rollback EXIT

docker run -d \
  --name "$name" \
  --restart unless-stopped \
  --env-file "$env_file" \
  --env VM_MANAGER_LOG_FILE=/data/current.log \
  -v /opt/migrated/vmmanager/data:/data \
  -v /opt/migrated/vmmanager/azure:/root/.azure \
  -p 192.168.178.204:8000:8000 \
  "$image" >/dev/null

ready=false
for _ in {1..30}; do
  if curl --fail --silent --max-time 2 "$url/healthz" >/dev/null &&
     curl --fail --silent --max-time 5 "$url/" >/dev/null; then ready=true; break; fi
  sleep 1
done
"$ready" || { echo 'VMManager did not become ready' >&2; exit 1; }

trap - EXIT
if "$had_previous"; then docker rm "$backup" >/dev/null; fi
docker tag "$image" local/vmmanager:vps
echo "Deployed VMManager $sha"
