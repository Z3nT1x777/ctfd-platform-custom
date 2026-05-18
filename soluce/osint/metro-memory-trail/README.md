# Writeup — Metro Memory Trail

**Catégorie** : OSINT  
**Difficulté** : Easy  
**Points** : 150  
**Flag** : `CTF{paris_bastille_1989}`

## Contexte

Un informateur a uploadé deux photos avant de disparaître. Ces images semblent anodines, mais leurs **métadonnées EXIF** contiennent les deux indices nécessaires :
- `clue.jpg` → coordonnées GPS cachées dans les métadonnées
- `final.jpg` → date de prise de vue cachée dans les métadonnées

## Étapes de résolution

### 1. Accéder à la page du challenge

```
http://192.168.56.10/osint/metro-memory-trail/resources/
```

On voit deux images présentées : une photo de station de métro et un tableau historique.

### 2. Extraire les métadonnées EXIF de clue.jpg

**Avec exiftool (en local) :**
```bash
exiftool clue.jpg
```

**Ou en ligne :** uploader `clue.jpg` sur [exifmeta.com](https://exifmeta.com) ou [metadata2go.com](https://www.metadata2go.com).

Résultat (extrait) :
```
GPS Latitude Ref  : North
GPS Latitude      : 48 deg 51' 11.88" N
GPS Longitude Ref : East
GPS Longitude     : 2 deg 22' 9.12" E
```

### 3. Identifier le lieu via les coordonnées GPS

Copier les coordonnées dans Google Maps :
```
48.8533, 2.3692
```

→ Google Maps indique **Place de la Bastille, Paris** → lieu = `paris_bastille`

### 4. Extraire la date de final.jpg

**Avec exiftool :**
```bash
exiftool final.jpg
```

Résultat (extrait) :
```
Date/Time Original : 1989:07:14 12:00:00
```

→ Année = `1989`

> **Note** : la date `1989-07-14` correspond au **14 juillet 1989**, bicentenaire de la prise de la Bastille — cohérent avec le lieu trouvé.

### 5. Construire le flag

Format : `CTF{ville_lieu_AAAA}`

```
ville = paris
lieu  = bastille
année = 1989
```

```
CTF{paris_bastille_1989}
```

## Outils utilisés

| Outil | Usage |
|---|---|
| [exifmeta.com](https://exifmeta.com) | Extraction EXIF en ligne |
| [metadata2go.com](https://www.metadata2go.com) | Alternative EXIF en ligne |
| Google Maps | Géolocalisation des coordonnées GPS |
| `exiftool` (CLI) | `exiftool <fichier>` pour tout afficher |

**En une ligne avec exiftool :**
```bash
exiftool clue.jpg | grep -i gps
exiftool final.jpg | grep -i date
```

## Explication pédagogique

Les fichiers JPEG embarquent un segment EXIF (Exchangeable Image File Format) qui peut contenir des dizaines de champs : appareil photo, paramètres d'exposition, logiciel utilisé, **coordonnées GPS**, et **date/heure de prise de vue**.

Ces métadonnées sont invisibles à l'œil nu mais accessibles avec n'importe quel lecteur EXIF. Dans un contexte OSINT réel, les photos partagées sur les réseaux sociaux (avant que les plateformes les strippent) ou envoyées par email conservent souvent ces informations — permettant de géolocaliser quelqu'un ou de dater précisément une prise de vue.

## Références

- [ExifTool documentation](https://exiftool.org/)
- [Wikipedia — Exchangeable image file format](https://en.wikipedia.org/wiki/Exif)
- MITRE ATT&CK T1592 (Gather Victim Host Information) : https://attack.mitre.org/techniques/T1592/
