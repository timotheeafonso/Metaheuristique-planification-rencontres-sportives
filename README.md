# Guide d'utilisation - Planification de Rencontres Sportives

Le code fourni permet d'appliquer la recherche locale avec la méthode de descente au problème de la planification de rencontres sportives. Le fichier s'appelle "tournament.py". Pour exécuter le fichier dans un environnement Linux, suivez les étapes suivantes :

## Installation des prérequis
Avant de commencer, assurez-vous d'avoir Python et PuLP installés. Pour installer PuLP, exécutez la commande suivante :

```shell
pip install pulp
```

## Exécution du code
1. Placez-vous dans le répertoire du fichier "tournament.py".
2. Lancez la commande suivante pour exécuter le code avec le nombre d'équipes de votre choix. Par exemple, pour un tournoi de 6 équipes :

```shell
python3 tournament.py 6
```

Si vous souhaitez mesurer le temps de résolution, exécutez la commande suivante :

```shell
time python3 tournament.py 6
```

Assurez-vous que le nombre d'équipes que vous spécifiez est pair.
