# Argo CD Dependency CMP

**Flux-style dependency management for Argo CD.**

## 🚀 Why this exists

Argo CD handles resource ordering using **Sync Waves** (`argocd.argoproj.io/sync-wave`). While powerful, managing these integers manually becomes a headache in complex applications. You often find yourself manually calculating: *"Database is wave 0, Migration is wave 1, Backend is wave 2..."*

If you have used **Flux**, you might miss the `dependsOn` feature, which allows you to explicitly state that Resource A depends on Resource B, letting the controller figure out the order.

**argocd-dependency-cmp** brings this capability to Argo CD. It acts as a sidecar plugin that:
1.  Scans your manifests (Raw YAML or Kustomize).
2.  Builds a Directed Acyclic Graph (DAG) based on a custom `depends-on` annotation.
3.  Automatically calculates and injects the correct `sync-wave` integer into your resources before Argo CD applies them.

## ✨ Features

* **Explicit Dependencies:** Define relationships like `my-org/depends-on: "Deployment:backend"`.
* **Automatic Sync Waves:** No more manual integer management.
* **Kustomize Support:** Automatically detects `kustomization.yaml` and builds it.
* **Recursive Discovery:** Can scan subdirectories for manifests.
* **Flexible Filtering:** Include or exclude files using glob patterns.

## 📦 Installation

To use this plugin, you must run it as a sidecar container in your `argocd-repo-server`.

If you are using the **Argo CD Helm Chart**, add the following to your `values.yaml`:

```yaml
repoServer:
  extraContainers:
    - name: dependency-cmp
      command: [/var/run/argocd/argocd-cmp-server]
      image: ghcr.io/notniknot/argocd-dependency-cmp:latest
      securityContext:
        runAsNonRoot: true
        runAsUser: 999
      volumeMounts:
        - mountPath: /var/run/argocd
          name: var-files
        - mountPath: /home/argocd/cmp-server/plugins
          name: plugins
```