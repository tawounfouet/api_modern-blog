#!/usr/bin/env python
"""
Script pour corriger l'affichage du logo dans l'interface d'administration Django
"""
import os
import sys
import django

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from admin_interface.models import Theme

def fix_logo_display():
    """Corrige l'affichage du logo en mettant à jour le CSS du thème actif"""
    
    css_fix = '''
        /* Force l'affichage du logo */
        #site-name .logo {
            display: inline-block !important;
            max-height: 40px;
            max-width: 150px;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        /* Améliore l'apparence du header avec le logo */
        #site-name a {
            display: flex;
            align-items: center;
            text-decoration: none;
        }
        
        /* Style pour le titre à côté du logo */
        #site-name span {
            font-size: 18px;
            font-weight: bold;
            margin-left: 8px;
        }
    '''
    
    try:
        # Récupérer le thème actif
        active_theme = Theme.objects.filter(active=True).first()
        
        if active_theme:
            print(f"Thème actif trouvé: {active_theme.name}")
            print(f"Logo visible actuel: {active_theme.logo_visible}")
            print(f"Logo actuel: {active_theme.logo}")
            
            # Mettre à jour la configuration
            active_theme.logo_visible = True
            active_theme.css = css_fix
            active_theme.save()
            
            print("✅ Configuration du thème mise à jour avec succès!")
            print("Le logo devrait maintenant s'afficher correctement.")
            
        else:
            print("❌ Aucun thème actif trouvé")
            
            # Créer un thème si aucun n'existe
            themes = Theme.objects.all()
            if themes.exists():
                theme = themes.first()
                theme.active = True
                theme.logo_visible = True
                theme.css = css_fix
                theme.save()
                print(f"✅ Thème '{theme.name}' activé et configuré")
            else:
                print("❌ Aucun thème disponible")
                
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")

if __name__ == "__main__":
    fix_logo_display()
