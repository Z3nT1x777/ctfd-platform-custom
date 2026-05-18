# Writeup — First Hacker

**Catégorie** : OSINT  
**Difficulté** : Easy  
**Points** : 100  
**Flag** : `CTF{kevin_mitnick}`

## Contexte

Un dossier classifié décrit un hacker légendaire des années 80 à travers une série d'indices. Il faut identifier la personne et soumettre son nom complet en minuscules.

## Indices fournis dans le challenge

```
- Condamné pour accès non autorisé à des systèmes d'entreprise à Los Angeles dans les années 80
- Spécialiste reconnu de l'ingénierie sociale
- Considéré comme l'un des hackers les plus recherchés des États-Unis
- A passé plusieurs années en fuite avant d'être finalement arrêté
- A collaboré avec les autorités après sa libération et est devenu consultant renommé en cybersécurité
- Décédé en juillet 2023
```

## Étapes de résolution

### 1. Recherche à partir des indices

Requête Google/Wikipedia :
```
hacker social engineering années 80 Los Angeles consultant cybersécurité décédé 2023
```

ou
```
most wanted hacker 1980s Los Angeles social engineering died 2023
```

### 2. Résultats

Les premiers résultats pointent tous vers **Kevin Mitnick** :

- Article Wikipedia : *Kevin Mitnick* — "American computer security consultant, author, and convicted hacker"
- Arrêté en 1995 après des années en fuite
- Condamné pour fraude informatique (accès non autorisé à des systèmes de Motorola, Nokia, etc.)
- Devenu consultant en cybersécurité et conférencier après sa libération (2000)
- Décédé le **16 juillet 2023** d'un cancer du pancréas

### 3. Vérification des indices

| Indice | Kevin Mitnick |
|---|---|
| Années 80, Los Angeles | ✅ Premier hack à LA en 1981 (Pacific Bell) |
| Ingénierie sociale | ✅ Auteur de "The Art of Deception" |
| Plus recherché des USA | ✅ Classé "most wanted" par le FBI |
| En fuite puis arrêté | ✅ 2,5 ans en fuite, arrêté en 1995 |
| Consultant cybersécurité | ✅ Fondateur de Mitnick Security Consulting |
| Décédé juillet 2023 | ✅ 16 juillet 2023 |

### 4. Construire le flag

Format : `CTF{prenom_nom}` (tout en minuscules, séparés par underscore)

```
prénom : kevin
nom    : mitnick
```

```
CTF{kevin_mitnick}
```

## Explication pédagogique

Ce challenge illustre la base de l'OSINT : **corréler plusieurs indices publics** pour identifier une personne. Chaque indice seul est insuffisant, mais leur combinaison pointe vers une cible unique. C'est exactement la méthode utilisée dans les investigations réelles — journalistiques, judiciaires, ou de renseignement.

Kevin Mitnick est une figure incontournable de l'histoire du hacking : ses exploits ont conduit les États-Unis à adopter des lois informatiques spécifiques, et il est l'auteur de deux livres de référence sur l'ingénierie sociale (*The Art of Deception*, *The Art of Intrusion*).

## Références

- Wikipedia — Kevin Mitnick : https://en.wikipedia.org/wiki/Kevin_Mitnick
- *The Art of Deception* (Kevin Mitnick, 2002)
- MITRE ATT&CK T1598 (Phishing for Information / Social Engineering) : https://attack.mitre.org/techniques/T1598/
