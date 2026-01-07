# Database Setup Guide

## Architecture Overview

La nouvelle architecture utilise **SQLite** avec **SQLAlchemy ORM** et le **pattern Repository** pour une meilleure organisation et maintenabilité.

```
database/
├── __init__.py                 # Exports principaux
├── config.py                   # Configuration SQLAlchemy & session
├── models.py                   # Modèles SQLAlchemy
├── adapter.py                  # Adaptateur pour compatibilité
├── seed.py                     # Script de population
└── repositories/
    ├── __init__.py
    ├── base.py                 # Repository de base
    ├── user_repository.py      # Opérations utilisateurs
    ├── clause_repository.py    # Opérations clauses légales
    ├── ticket_repository.py    # Opérations tickets Jira
    ├── invoice_repository.py   # Opérations factures
    └── audit_repository.py     # Opérations logs d'audit
```

## Installation

### 1. Installer les dépendances

```bash
pip install sqlalchemy alembic
```

### 2. Initialiser la base de données

```bash
# Créer les tables et insérer les données initiales
python -m database.seed
```

Cela va créer le fichier `legal_billing.db` avec toutes les tables et données de test.

## Utilisation

### Option 1: Utiliser l'adaptateur (Compatible avec le code existant)

```python
from database.adapter import db

# Les méthodes restent identiques
user = db.get_user("user_001")
clauses = db.list_clauses(active_only=True)
tickets = db.get_jira_tickets(status=TicketStatus.CLOSED)
```

**Avantage**: Aucun changement dans votre code existant !

### Option 2: Utiliser les repositories directement (Recommandé pour nouveau code)

```python
from database import get_db, UserRepository

def my_endpoint(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get("user_001")
    return user
```

**Avantages**:
- Gestion automatique des sessions
- Transactions automatiques
- Meilleure testabilité
- Performance optimisée

## Exemples d'utilisation des Repositories

### User Repository

```python
from database import get_db, UserRepository

db = next(get_db())
user_repo = UserRepository(db)

# Créer un utilisateur
user = user_repo.create({
    "user_id": "user_004",
    "name": "Alice Cooper",
    "email": "alice@example.com",
    "role": UserRoleEnum.PROJECT_LEADER
})

# Récupérer par email
user = user_repo.get_by_email("alice@example.com")

# Mettre à jour le token Jira
user_repo.update_jira_token("user_004", "my_encrypted_token")
```

### Clause Repository

```python
from database import ClauseRepository

clause_repo = ClauseRepository(db)

# Récupérer les clauses actives
active_clauses = clause_repo.get_active_clauses()

# Désactiver une clause
clause_repo.deactivate("FLASH_001")

# Récupérer par label
clause = clause_repo.get_by_label("FLASH_002")
```

### Ticket Repository

```python
from database import TicketRepository

ticket_repo = TicketRepository(db)

# Récupérer par statut
closed_tickets = ticket_repo.get_by_status(TicketStatusEnum.CLOSED)

# Récupérer par période
tickets = ticket_repo.get_by_date_range(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Mettre à jour les infos de facturation
ticket_repo.update_billing_info(
    ticket_id="BMW-101",
    clause_id="FLASH_001",
    billable_amount=1402.50,
    is_billable=True
)

# Création en masse
ticket_repo.bulk_create([
    {"ticket_id": "BMW-200", "summary": "...", ...},
    {"ticket_id": "BMW-201", "summary": "...", ...}
])
```

### Invoice Repository

```python
from database import InvoiceRepository

invoice_repo = InvoiceRepository(db)

# Créer une facture avec lignes
invoice = invoice_repo.create_with_lines(
    invoice_data={
        "invoice_id": "INV-2025-01-001",
        "project_name": "BMW FLASH",
        "billing_period": "2025-01",
        "total_amount": Decimal("5000.00"),
        "currency": CurrencyEnum.EUR,
        "status": InvoiceStatusEnum.DRAFT,
        "created_by": "user_001"
    },
    lines_data=[
        {
            "jira_ticket_id": "BMW-101",
            "clause_id": "FLASH_001",
            "hours_worked": Decimal("50.0"),
            "unit_price": Decimal("85.00"),
            "line_total": Decimal("4250.00")
        }
    ]
)

# Récupérer avec lignes chargées
invoice = invoice_repo.get_with_lines("INV-2025-01-001")

# Statistiques
stats = invoice_repo.get_statistics(user_id="user_001")
# Returns: {'total_invoices': 5, 'total_amount': 12500.00, 'by_status': {...}}
```

### Audit Repository

```python
from database import AuditRepository

audit_repo = AuditRepository(db)

# Logger une action
audit_repo.log_action(
    user_id="user_001",
    action="GENERATE_INVOICE",
    details="Generated invoice INV-2025-01-001"
)

# Récupérer les logs récents
recent_logs = audit_repo.get_recent(limit=100)

# Récupérer par utilisateur
user_logs = audit_repo.get_by_user("user_001")
```

## Migration depuis MockDatabase

### Avant (MockDatabase)
```python
from database import db

user = db.get_user("user_001")
clauses = db.list_clauses()
```

### Après (Avec Adapter - Aucun changement !)
```python
from database.adapter import db

user = db.get_user("user_001")  # Même interface !
clauses = db.list_clauses()     # Fonctionne pareil !
```

### Après (Repositories - Nouvelle façon)
```python
from database import get_db, UserRepository, ClauseRepository
from fastapi import Depends

def my_endpoint(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    clause_repo = ClauseRepository(db)
    
    user = user_repo.get("user_001")
    clauses = clause_repo.get_active_clauses()
```

## Configuration

### Variables d'environnement

```bash
# .env file
DATABASE_URL=sqlite:///./legal_billing.db

# Pour PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost/legal_billing

# Pour MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost/legal_billing
```

### Configuration personnalisée

```python
# config.py
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./legal_billing.db"  # Valeur par défaut
)

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Active les logs SQL (développement)
    pool_size=10,  # Taille du pool de connexions
    max_overflow=20
)
```

## Tests

### Tester la connexion

```python
from database import init_db, SessionLocal

# Initialiser
init_db()

# Créer une session
db = SessionLocal()

try:
    # Tester une requête
    from database.models import UserModel
    users = db.query(UserModel).all()
    print(f"Found {len(users)} users")
finally:
    db.close()
```

### Reset de la base de données

```python
from database import drop_db, init_db
from database.seed import seed_database

# Attention: Supprime toutes les données !
drop_db()
init_db()
seed_database()
```

## Bonnes pratiques

### 1. Toujours utiliser des sessions contextuelles

```python
# ✅ BON
from database import get_db

def my_function(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get("user_001")

# ❌ MAUVAIS
from database import SessionLocal
db = SessionLocal()  # Jamais fermée !
```

### 2. Gérer les transactions

```python
from database import SessionLocal

db = SessionLocal()
try:
    # Opérations multiples
    user_repo.create({...})
    clause_repo.create({...})
    db.commit()  # Commit explicite
except Exception as e:
    db.rollback()  # Rollback en cas d'erreur
    raise e
finally:
    db.close()
```

### 3. Utiliser les repositories pour la logique métier

```python
# ✅ BON - Logique dans le repository
class InvoiceRepository:
    def get_monthly_total(self, month: str) -> Decimal:
        return self.db.query(func.sum(InvoiceModel.total_amount))\
            .filter(InvoiceModel.billing_period == month)\
            .scalar() or Decimal("0.00")

# ❌ MAUVAIS - Logique dans le contrôleur
total = sum(inv.total_amount for inv in invoices)
```

## Troubleshooting

### Erreur: "database is locked"

```bash
# SQLite ne supporte qu'un seul writer
# Solution: Utiliser PostgreSQL pour la production
DATABASE_URL=postgresql://...
```

### Erreur: "No such table"

```bash
# Initialiser la base de données
python -m database.seed
```

### Performances lentes

```python
# Utiliser eager loading pour les relations
invoice = db.query(InvoiceModel)\
    .options(joinedload(InvoiceModel.lines))\
    .filter(InvoiceModel.invoice_id == id)\
    .first()
```

## Prochaines étapes

1. ✅ Base de données SQLite configurée
2. ✅ Repositories implémentés
3. ✅ Adapter pour compatibilité
4. 🔄 Migrer progressivement vers les repositories
5. 📦 Ajouter Alembic pour les migrations
6. 🚀 Migrer vers PostgreSQL pour la production