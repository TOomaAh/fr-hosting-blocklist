# fr-hosting-blocklist

Listes IPv4/IPv6 des préfixes annoncés par les principaux hébergeurs français, à utiliser comme **Network List dynamique** dans UniFi Network 11 (ou tout pare-feu acceptant une liste d'IP/CIDR par URL).

## Fichiers

| Fichier | Contenu |
|---|---|
| `asns.txt` | ASN suivis (à éditer) |
| `output/ipv4.txt` | Préfixes IPv4 agrégés, un CIDR par ligne |
| `output/ipv6.txt` | Préfixes IPv6 agrégés, un CIDR par ligne |
| `scripts/generate.py` | Générateur (stdlib Python, source RIPEstat) |

## Fonctionnement

- Une GitHub Action tourne chaque jour, et à chaque modification de `asns.txt`.
- Les préfixes sont récupérés via l'API RIPEstat `announced-prefixes`, puis agrégés.
- **Garde-fou** : si une liste devient vide ou perd plus de 50 % de ses entrées, le job échoue et l'ancienne liste est conservée (une liste vide désactiverait le blocage).

## Utilisation dans UniFi Network 11

1. `Networks > Network Lists > Create New`
2. Type : **IPv4** (créer une seconde liste pour l'IPv6 si besoin), Source : **Dynamic**
3. URL : `https://raw.githubusercontent.com/<user>/fr-hosting-blocklist/main/output/ipv4.txt`
4. Rafraîchissement : 24 h
5. Utiliser la liste comme **source** d'une règle `External → Internal` / `External → Gateway` en **Block**.

> À utiliser en entrée uniquement : en sortie, ça bloquerait l'accès à tous les sites hébergés chez ces fournisseurs.

## Ajouter un hébergeur

Ajouter son ASN dans `asns.txt` (vérifier sur https://bgp.he.net), commit, push : le workflow régénère les listes.

## Lancer en local

```bash
python3 scripts/generate.py
```
