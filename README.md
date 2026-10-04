# z-scanner-RTSP

Petit scanner Python qui compte les hôtes actifs sur le réseau local et repère ceux qui acceptent les connexions RTSP sur TCP/554.

## Utilisation

```bash
python3 z-scanner-RTSP.py 192.168.0.1
```

Une adresse sans masque est interprétée comme un réseau `/24` (ici `192.168.0.0/24`). Pour préciser un autre sous-réseau, indiquez-le en CIDR :

```bash
python3 z-scanner-RTSP.py 192.168.1.0/24
```

Le script affiche le nombre d'adresses IP actives (réponse au ping ou port 554 ouvert), ainsi que les adresses dont TCP/554 est ouvert. Un hôte qui bloque le ping et n'a pas TCP/554 ouvert ne peut pas être détecté comme actif. Options disponibles : `--timeout` (délai de connexion, en secondes) et `--workers` (connexions simultanées). Il ne demande ni ne stocke de mot de passe.
