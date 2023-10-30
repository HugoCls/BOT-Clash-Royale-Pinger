# Initialisez un dictionnaire vide pour stocker les paires login:pass
sensitive_data = {}

# Ouvrez le fichier en mode lecture
with open('data/sensitive_data.txt', 'r') as file:
    # Lisez chaque ligne du fichier
    for line in file:
        # Divisez la ligne en utilisant ':' comme séparateur
        parts = line.strip().split(':')
        # Assurez-vous qu'il y a deux parties (login et mot de passe)
        if len(parts) == 2:
            name, value = parts[0], parts[1]
            # Ajoutez la paire login:pass au dictionnaire
            sensitive_data[name] = value