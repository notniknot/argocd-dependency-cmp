# argocd-dependency-cmp
A Config Management Plugin for ArgoCD to handle dependencies similar to Flux


https://argo-cd.readthedocs.io/en/stable/user-guide/tool_detection/


argocd monorepo controller
controller.diff.server.side: "true"
shallow clone in 3.3 for mono repos
no prune for root +  team apps


argocd-apps/...
applications/...

can we create a cross region private network and attach multiple clusters from different regions?
argocd preview diff in PR


export CR_PAT=xxx
echo $CR_PAT | podman login ghcr.io -u notniknot --password-stdin


podman build \                  
  --platform="linux/amd64" \
  -t ghcr.io/notniknot/argocd-dependency-cmp:v1 \
  -t ghcr.io/notniknot/argocd-dependency-cmp:latest \
  -f Containerfile \
  .

podman push ghcr.io/notniknot/argocd-dependency-cmp:v1  
podman push ghcr.io/notniknot/argocd-dependency-cmp:latest


uv run ~/projects/combine_files.py ./docs/docs ./combined -x -e .md