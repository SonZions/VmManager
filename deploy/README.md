# VPS deployment

The `Deploy VMManager to VPS` workflow runs manually on `main`. Its GitHub
runner must be registered only for `SonZions/VmManager` with labels `my-vps`
and `vmmanager`. The runner invokes the root-owned
`/usr/local/sbin/vmmanager-vps-deploy` bridge; it does not need Docker access
or read access to `/etc/migrated-containers`.

The bridge fetches `origin/main` in `/opt/vps-deploy/vmmanager/repo`, requires
it to match the workflow commit, builds the image into local Docker, and
replaces `vmmanager-vps`. It keeps the former container until `/healthz` and
the UI root route are ready. On a failed start it restores the former
container. The existing VPN-only port, data and Azure mounts, and root-owned
env file remain in use.

The bridge is installed separately from the Git checkout. Changes to
`deploy/vps-deploy.sh` require review and a root-owned reinstall on the VPS.
