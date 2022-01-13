#!env zsh

# Script d'ouverture du programme d'édition pour débogage

python3.9 -m pip install --upgrade spyder # Mise à jour de Spyder au cas où
spyder -p . & # Lancer Spyder en arrière plan
