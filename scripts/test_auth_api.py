#!/usr/bin/env python3
"""
Script de test pour l'API d'authentification de Modern Blog Platform
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8001/api/auth"
TEST_USER = {
    "username": "testapi",
    "email": "testapi@example.com",
    "password1": "testpassword123",
    "password2": "testpassword123",
    "first_name": "Test",
    "last_name": "API",
}


def print_test(test_name, success=True, details=""):
    """Affiche le résultat d'un test"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")
    print()


def test_registration():
    """Test d'inscription"""
    print("🔹 Test d'inscription...")
    try:
        response = requests.post(f"{BASE_URL}/registration/", json=TEST_USER)
        if response.status_code == 201:
            print_test("Inscription réussie", True, "Utilisateur créé avec succès")
            return True
        else:
            print_test(
                "Inscription échouée",
                False,
                f"Status: {response.status_code}, Response: {response.text}",
            )
            return False
    except Exception as e:
        print_test("Inscription échouée", False, f"Erreur: {e}")
        return False


def test_login():
    """Test de connexion"""
    print("🔹 Test de connexion...")
    try:
        login_data = {"email": TEST_USER["email"], "password": TEST_USER["password1"]}
        response = requests.post(f"{BASE_URL}/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            if "access" in data and "user" in data:
                print_test("Connexion réussie", True, "Token JWT obtenu")
                return data["access"]
            else:
                print_test(
                    "Connexion échouée", False, "Réponse manquante: access ou user"
                )
                return None
        else:
            print_test(
                "Connexion échouée",
                False,
                f"Status: {response.status_code}, Response: {response.text}",
            )
            return None
    except Exception as e:
        print_test("Connexion échouée", False, f"Erreur: {e}")
        return None


def test_user_info(token):
    """Test récupération info utilisateur"""
    print("🔹 Test récupération informations utilisateur...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/user/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "profile" in data and data["email"] == TEST_USER["email"]:
                print_test(
                    "Récupération info utilisateur",
                    True,
                    "Données utilisateur et profil récupérées",
                )
                return True
            else:
                print_test(
                    "Récupération info utilisateur",
                    False,
                    "Données manquantes dans la réponse",
                )
                return False
        else:
            print_test(
                "Récupération info utilisateur",
                False,
                f"Status: {response.status_code}",
            )
            return False
    except Exception as e:
        print_test("Récupération info utilisateur", False, f"Erreur: {e}")
        return False


def test_profile_get(token):
    """Test récupération profil"""
    print("🔹 Test récupération profil...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/profile/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "bio" in data and "role" in data:
                print_test("Récupération profil", True, "Profil détaillé récupéré")
                return True
            else:
                print_test("Récupération profil", False, "Champs profil manquants")
                return False
        else:
            print_test("Récupération profil", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Récupération profil", False, f"Erreur: {e}")
        return False


def test_profile_update(token):
    """Test mise à jour profil"""
    print("🔹 Test mise à jour profil...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        profile_data = {
            "bio": "Profil de test mis à jour",
            "website": "https://test-api.example.com",
            "location": "Test City",
            "role": "author",
            "headline": "API Tester",
            "interests": "Testing, API, Django",
        }
        response = requests.put(
            f"{BASE_URL}/profile/update/", json=profile_data, headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            if (
                data.get("bio") == profile_data["bio"]
                and data.get("role") == profile_data["role"]
            ):
                print_test("Mise à jour profil", True, "Profil mis à jour avec succès")
                return True
            else:
                print_test(
                    "Mise à jour profil", False, "Données non mises à jour correctement"
                )
                return False
        else:
            print_test(
                "Mise à jour profil",
                False,
                f"Status: {response.status_code}, Response: {response.text}",
            )
            return False
    except Exception as e:
        print_test("Mise à jour profil", False, f"Erreur: {e}")
        return False


def test_logout(token):
    """Test déconnexion"""
    print("🔹 Test déconnexion...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/logout/", headers=headers)
        if response.status_code == 200:
            print_test("Déconnexion", True, "Déconnexion réussie")
            return True
        else:
            print_test("Déconnexion", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Déconnexion", False, f"Erreur: {e}")
        return False


def test_token_after_logout(token):
    """Test que le token ne fonctionne plus après déconnexion"""
    print("🔹 Test invalidation token après déconnexion...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/user/", headers=headers)
        if response.status_code == 401:
            print_test("Invalidation token", True, "Token correctement invalidé")
            return True
        else:
            print_test(
                "Invalidation token",
                False,
                f"Token encore valide: {response.status_code}",
            )
            return False
    except Exception as e:
        print_test("Invalidation token", False, f"Erreur: {e}")
        return False


def cleanup_test_user():
    """Nettoie l'utilisateur de test (nécessite accès direct à la DB)"""
    print("🔹 Nettoyage utilisateur de test...")
    # Cette fonction nécessiterait Django shell ou accès direct à la DB
    # Pour simplifier, on l'ignore pour l'instant
    pass


def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🚀 TESTS DE L'API D'AUTHENTIFICATION")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print()

    # Variables pour suivre les résultats
    tests_passed = 0
    total_tests = 7
    access_token = None

    # 1. Test d'inscription
    if test_registration():
        tests_passed += 1

    # 2. Test de connexion
    access_token = test_login()
    if access_token:
        tests_passed += 1

        # 3. Test récupération info utilisateur
        if test_user_info(access_token):
            tests_passed += 1

        # 4. Test récupération profil
        if test_profile_get(access_token):
            tests_passed += 1

        # 5. Test mise à jour profil
        if test_profile_update(access_token):
            tests_passed += 1

        # 6. Test déconnexion
        if test_logout(access_token):
            tests_passed += 1

        # 7. Test invalidation token
        if test_token_after_logout(access_token):
            tests_passed += 1

    # Résumé des tests
    print("=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"✅ Tests réussis: {tests_passed}/{total_tests}")
    print(f"❌ Tests échoués: {total_tests - tests_passed}/{total_tests}")

    success_rate = (tests_passed / total_tests) * 100
    print(f"📈 Taux de réussite: {success_rate:.1f}%")

    if tests_passed == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
