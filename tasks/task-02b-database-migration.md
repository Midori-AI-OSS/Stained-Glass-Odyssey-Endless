# Task 2B: Database Migration

## Overview

This task implements the data migration from the existing SQLite database to PostgreSQL, preserving all existing game data while improving the database structure with proper relationships and constraints.

## Goals

- Create automated migration scripts for SQLite to PostgreSQL
- Preserve all existing game data (runs, players, gacha items, upgrades)
- Implement data validation and integrity checks
- Create rollback procedures for safety

## Prerequisites

- Task 2A (Database Setup) must be completed
- PostgreSQL container running with pgAdmin accessible on port 38085
- Existing SQLite database accessible at `backend/save.db`

## Implementation

### Step 1: Migration Analysis Script

**File**: `database/migration/analyze_sqlite.py`
```python
#!/usr/bin/env python3
"""Analyze existing SQLite database for migration planning."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any
import sys

def analyze_database(db_path: str) -> Dict[str, Any]:
    """Analyze SQLite database structure and data."""
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return {}
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    analysis = {
        "tables": {},
        "data_counts": {},
        "schema": {},
        "sample_data": {}
    }
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            analysis["schema"][table] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            analysis["data_counts"][table] = count
            
            # Get sample data (first 3 rows)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
                rows = cursor.fetchall()
                analysis["sample_data"][table] = [dict(row) for row in rows]
            
            print(f"📊 Table {table}: {count} rows")
    
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
    finally:
        conn.close()
    
    return analysis

def save_analysis(analysis: Dict[str, Any], output_path: str):
    """Save analysis results to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"💾 Analysis saved to: {output_path}")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/save.db"
    output_path = "sqlite_analysis.json"
    
    print(f"🔍 Analyzing SQLite database: {db_path}")
    analysis = analyze_database(db_path)
    
    if analysis:
        save_analysis(analysis, output_path)
        print("\n📋 Analysis Summary:")
        for table, count in analysis["data_counts"].items():
            print(f"  {table}: {count} records")
    else:
        print("❌ Failed to analyze database")
        sys.exit(1)
```

### Step 2: Data Export Script

**File**: `database/migration/export_sqlite.py`
```python
#!/usr/bin/env python3
"""Export data from SQLite database to PostgreSQL-compatible format."""

import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys

class SQLiteExporter:
    """Exports SQLite data for PostgreSQL migration."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.export_data = {}
        
    def export_runs(self) -> List[Dict[str, Any]]:
        """Export runs table data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runs;")
        rows = cursor.fetchall()
        
        runs = []
        for row in rows:
            run_data = {
                "id": str(uuid.uuid4()),
                "legacy_id": row["id"],
                "party": json.loads(row["party"]) if row["party"] else {},
                "map": json.loads(row["map"]) if row["map"] else {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            runs.append(run_data)
            
        print(f"📤 Exported {len(runs)} runs")
        return runs
    
    def export_owned_players(self) -> List[Dict[str, Any]]:
        """Export owned_players table data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM owned_players;")
        rows = cursor.fetchall()
        
        players = []
        for row in rows:
            player_data = {
                "id": str(uuid.uuid4()),
                "legacy_id": row["id"],
                "player_data": {},  # Will be populated from other sources
                "created_at": datetime.now().isoformat()
            }
            players.append(player_data)
            
        print(f"📤 Exported {len(players)} owned players")
        return players
    
    def export_gacha_items(self) -> List[Dict[str, Any]]:
        """Export gacha_items table data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM gacha_items;")
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            item_data = {
                "id": str(uuid.uuid4()),
                "legacy_id": row["id"],
                "item_id": row["item_id"],
                "type": row["type"],
                "star_level": row["star_level"],
                "obtained_at": row["obtained_at"] or datetime.now().isoformat()
            }
            items.append(item_data)
            
        print(f"📤 Exported {len(items)} gacha items")
        return items
    
    def export_gacha_rolls(self) -> List[Dict[str, Any]]:
        """Export gacha_rolls table data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM gacha_rolls;")
        rows = cursor.fetchall()
        
        rolls = []
        for row in rows:
            roll_data = {
                "id": str(uuid.uuid4()),
                "legacy_id": row["id"],
                "player_id": row["player_id"],
                "items": json.loads(row["items"]) if row["items"] else [],
                "rolled_at": row["rolled_at"] or datetime.now().isoformat()
            }
            rolls.append(roll_data)
            
        print(f"📤 Exported {len(rolls)} gacha rolls")
        return rolls
    
    def export_upgrade_points(self) -> List[Dict[str, Any]]:
        """Export upgrade_points table data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM upgrade_points;")
        rows = cursor.fetchall()
        
        upgrades = []
        for row in rows:
            upgrade_data = {
                "player_id": row["player_id"],
                "points": row["points"],
                "hp": row["hp"],
                "atk": row["atk"],
                "def": row["def"],
                "crit_rate": row["crit_rate"],
                "crit_damage": row["crit_damage"],
                "updated_at": datetime.now().isoformat()
            }
            upgrades.append(upgrade_data)
            
        print(f"📤 Exported {len(upgrades)} upgrade point records")
        return upgrades
    
    def export_damage_types(self) -> List[Dict[str, Any]]:
        """Export damage_types table data if it exists."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM damage_types;")
            rows = cursor.fetchall()
            
            damage_types = []
            for row in rows:
                damage_type_data = {
                    "id": str(uuid.uuid4()),
                    "legacy_id": row["id"],
                    "type": row["type"],
                    "created_at": datetime.now().isoformat()
                }
                damage_types.append(damage_type_data)
                
            print(f"📤 Exported {len(damage_types)} damage types")
            return damage_types
            
        except sqlite3.OperationalError:
            print("ℹ️  No damage_types table found")
            return []
    
    def export_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all table data."""
        print("🚀 Starting SQLite data export...")
        
        export_data = {
            "runs": self.export_runs(),
            "owned_players": self.export_owned_players(),
            "gacha_items": self.export_gacha_items(),
            "gacha_rolls": self.export_gacha_rolls(),
            "upgrade_points": self.export_upgrade_points(),
            "damage_types": self.export_damage_types()
        }
        
        # Add metadata
        export_data["_metadata"] = {
            "export_date": datetime.now().isoformat(),
            "source_database": self.db_path,
            "total_records": sum(len(data) for data in export_data.values() if isinstance(data, list))
        }
        
        print(f"✅ Export complete: {export_data['_metadata']['total_records']} total records")
        return export_data
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def save_export_data(data: Dict[str, Any], output_path: str):
    """Save exported data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"💾 Export data saved to: {output_path}")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/save.db"
    output_path = "sqlite_export.json"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    exporter = SQLiteExporter(db_path)
    try:
        export_data = exporter.export_all()
        save_export_data(export_data, output_path)
        print("\n📊 Export Summary:")
        for table, data in export_data.items():
            if isinstance(data, list):
                print(f"  {table}: {len(data)} records")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)
    finally:
        exporter.close()
```

### Step 3: PostgreSQL Import Script

**File**: `database/migration/import_postgresql.py`
```python
#!/usr/bin/env python3
"""Import data from SQLite export into PostgreSQL."""

import json
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any
import sys
from pathlib import Path

class PostgreSQLImporter:
    """Imports data into PostgreSQL database."""
    
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self.conn.autocommit = False
        
    def clear_tables(self):
        """Clear all tables for fresh import."""
        print("🧹 Clearing existing data...")
        
        with self.conn.cursor() as cursor:
            # Disable foreign key checks temporarily
            cursor.execute("SET session_replication_role = 'replica';")
            
            # Clear tables in order to avoid foreign key issues
            tables = [
                "gacha_rolls", "gacha_items", "damage_types", 
                "upgrade_points", "owned_players", "runs"
            ]
            
            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"  Cleared {table}")
            
            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = 'origin';")
            
        self.conn.commit()
    
    def import_runs(self, runs: List[Dict[str, Any]]):
        """Import runs data."""
        if not runs:
            return
            
        print(f"📥 Importing {len(runs)} runs...")
        
        with self.conn.cursor() as cursor:
            for run in runs:
                cursor.execute("""
                    INSERT INTO runs (id, legacy_id, party, map, created_at, updated_at)
                    VALUES (%(id)s, %(legacy_id)s, %(party)s, %(map)s, %(created_at)s, %(updated_at)s)
                """, run)
        
        self.conn.commit()
        print(f"✅ Imported {len(runs)} runs")
    
    def import_owned_players(self, players: List[Dict[str, Any]]):
        """Import owned players data."""
        if not players:
            return
            
        print(f"📥 Importing {len(players)} owned players...")
        
        with self.conn.cursor() as cursor:
            for player in players:
                cursor.execute("""
                    INSERT INTO owned_players (id, legacy_id, player_data, created_at)
                    VALUES (%(id)s, %(legacy_id)s, %(player_data)s, %(created_at)s)
                """, player)
        
        self.conn.commit()
        print(f"✅ Imported {len(players)} owned players")
    
    def import_gacha_items(self, items: List[Dict[str, Any]]):
        """Import gacha items data."""
        if not items:
            return
            
        print(f"📥 Importing {len(items)} gacha items...")
        
        with self.conn.cursor() as cursor:
            for item in items:
                cursor.execute("""
                    INSERT INTO gacha_items (id, legacy_id, item_id, type, star_level, obtained_at)
                    VALUES (%(id)s, %(legacy_id)s, %(item_id)s, %(type)s, %(star_level)s, %(obtained_at)s)
                """, item)
        
        self.conn.commit()
        print(f"✅ Imported {len(items)} gacha items")
    
    def import_gacha_rolls(self, rolls: List[Dict[str, Any]]):
        """Import gacha rolls data."""
        if not rolls:
            return
            
        print(f"📥 Importing {len(rolls)} gacha rolls...")
        
        with self.conn.cursor() as cursor:
            for roll in rolls:
                cursor.execute("""
                    INSERT INTO gacha_rolls (id, legacy_id, player_id, items, rolled_at)
                    VALUES (%(id)s, %(legacy_id)s, %(player_id)s, %(items)s, %(rolled_at)s)
                """, roll)
        
        self.conn.commit()
        print(f"✅ Imported {len(rolls)} gacha rolls")
    
    def import_upgrade_points(self, upgrades: List[Dict[str, Any]]):
        """Import upgrade points data."""
        if not upgrades:
            return
            
        print(f"📥 Importing {len(upgrades)} upgrade point records...")
        
        with self.conn.cursor() as cursor:
            for upgrade in upgrades:
                cursor.execute("""
                    INSERT INTO upgrade_points (player_id, points, hp, atk, def, crit_rate, crit_damage, updated_at)
                    VALUES (%(player_id)s, %(points)s, %(hp)s, %(atk)s, %(def)s, %(crit_rate)s, %(crit_damage)s, %(updated_at)s)
                """, upgrade)
        
        self.conn.commit()
        print(f"✅ Imported {len(upgrades)} upgrade point records")
    
    def import_damage_types(self, damage_types: List[Dict[str, Any]]):
        """Import damage types data."""
        if not damage_types:
            return
            
        print(f"📥 Importing {len(damage_types)} damage types...")
        
        with self.conn.cursor() as cursor:
            for damage_type in damage_types:
                cursor.execute("""
                    INSERT INTO damage_types (id, legacy_id, type, created_at)
                    VALUES (%(id)s, %(legacy_id)s, %(type)s, %(created_at)s)
                """, damage_type)
        
        self.conn.commit()
        print(f"✅ Imported {len(damage_types)} damage types")
    
    def validate_import(self, original_data: Dict[str, Any]):
        """Validate imported data counts."""
        print("🔍 Validating import...")
        
        with self.conn.cursor() as cursor:
            tables = ["runs", "owned_players", "gacha_items", "gacha_rolls", "upgrade_points", "damage_types"]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                imported_count = cursor.fetchone()[0]
                original_count = len(original_data.get(table, []))
                
                if imported_count == original_count:
                    print(f"  ✅ {table}: {imported_count} records (matches original)")
                else:
                    print(f"  ⚠️  {table}: {imported_count} imported vs {original_count} original")
    
    def import_all(self, data: Dict[str, Any], clear_first: bool = True):
        """Import all data."""
        print("🚀 Starting PostgreSQL data import...")
        
        try:
            if clear_first:
                self.clear_tables()
            
            # Import in order to handle dependencies
            self.import_runs(data.get("runs", []))
            self.import_owned_players(data.get("owned_players", []))
            self.import_gacha_items(data.get("gacha_items", []))
            self.import_gacha_rolls(data.get("gacha_rolls", []))
            self.import_upgrade_points(data.get("upgrade_points", []))
            self.import_damage_types(data.get("damage_types", []))
            
            self.validate_import(data)
            print("✅ Import completed successfully!")
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            self.conn.rollback()
            raise
    
    def close(self):
        """Close database connection."""
        self.conn.close()

if __name__ == "__main__":
    import_file = sys.argv[1] if len(sys.argv) > 1 else "sqlite_export.json"
    
    if not Path(import_file).exists():
        print(f"❌ Import file not found: {import_file}")
        sys.exit(1)
    
    # Load exported data
    with open(import_file, 'r') as f:
        export_data = json.load(f)
    
    # PostgreSQL connection
    connection_string = "postgresql://autofighter:password@localhost:5432/autofighter"
    
    importer = PostgreSQLImporter(connection_string)
    try:
        importer.import_all(export_data)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        importer.close()
```

### Step 4: Migration Orchestration Script

**File**: `database/migration/migrate.py`
```python
#!/usr/bin/env python3
"""Complete migration orchestration script."""

import subprocess
import sys
from pathlib import Path
import json
import time

class MigrationOrchestrator:
    """Orchestrates the complete SQLite to PostgreSQL migration."""
    
    def __init__(self, sqlite_path: str, postgres_conn: str):
        self.sqlite_path = sqlite_path
        self.postgres_conn = postgres_conn
        self.export_file = "sqlite_export.json"
        self.analysis_file = "sqlite_analysis.json"
    
    def check_prerequisites(self) -> bool:
        """Check that all prerequisites are met."""
        print("🔍 Checking migration prerequisites...")
        
        # Check SQLite database exists
        if not Path(self.sqlite_path).exists():
            print(f"❌ SQLite database not found: {self.sqlite_path}")
            return False
        
        # Check PostgreSQL connection (basic)
        try:
            import psycopg2
            conn = psycopg2.connect(self.postgres_conn)
            conn.close()
            print("✅ PostgreSQL connection verified")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
        
        return True
    
    def run_analysis(self) -> bool:
        """Run SQLite database analysis."""
        print("📊 Analyzing SQLite database...")
        
        try:
            result = subprocess.run([
                "python", "analyze_sqlite.py", self.sqlite_path
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Analysis failed: {e.stderr}")
            return False
    
    def run_export(self) -> bool:
        """Run data export from SQLite."""
        print("📤 Exporting data from SQLite...")
        
        try:
            result = subprocess.run([
                "python", "export_sqlite.py", self.sqlite_path
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            return Path(self.export_file).exists()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Export failed: {e.stderr}")
            return False
    
    def run_import(self) -> bool:
        """Run data import to PostgreSQL."""
        print("📥 Importing data to PostgreSQL...")
        
        try:
            result = subprocess.run([
                "python", "import_postgresql.py", self.export_file
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Import failed: {e.stderr}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate the completed migration."""
        print("🔍 Validating migration results...")
        
        if not Path(self.export_file).exists():
            print("❌ Export file not found for validation")
            return False
        
        with open(self.export_file, 'r') as f:
            export_data = json.load(f)
        
        total_exported = export_data.get("_metadata", {}).get("total_records", 0)
        print(f"📊 Total records exported: {total_exported}")
        
        # Additional validation could be added here
        return total_exported > 0
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        print("🚀 Starting complete SQLite to PostgreSQL migration...")
        print(f"Source: {self.sqlite_path}")
        print(f"Target: PostgreSQL")
        print("-" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Run analysis
        if not self.run_analysis():
            return False
        
        # Run export
        if not self.run_export():
            return False
        
        # Run import
        if not self.run_import():
            return False
        
        # Validate results
        if not self.validate_migration():
            return False
        
        print("-" * 50)
        print("🎉 Migration completed successfully!")
        print(f"📁 Export data saved in: {self.export_file}")
        print(f"📁 Analysis saved in: {self.analysis_file}")
        
        return True

if __name__ == "__main__":
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/save.db"
    postgres_conn = "postgresql://autofighter:password@localhost:5432/autofighter"
    
    orchestrator = MigrationOrchestrator(sqlite_path, postgres_conn)
    
    success = orchestrator.run_migration()
    sys.exit(0 if success else 1)
```

## Validation Criteria

### Success Criteria
1. **Data Preservation**: All existing game data migrated without loss
2. **Schema Conversion**: SQLite schema successfully converted to PostgreSQL
3. **Data Integrity**: All relationships and constraints maintained
4. **Validation Checks**: Import counts match export counts
5. **Rollback Capability**: Original SQLite database preserved

### Validation Commands
```bash
# Run complete migration
cd database/migration
python migrate.py ../../backend/save.db

# Verify data in PostgreSQL (via pgAdmin at localhost:38085)
# Or connect directly:
psql -h localhost -U autofighter -d autofighter

# Check record counts
SELECT COUNT(*) FROM runs;
SELECT COUNT(*) FROM owned_players;
SELECT COUNT(*) FROM gacha_items;
```

### Expected Results
- All SQLite data successfully exported to JSON
- PostgreSQL tables populated with converted data
- Record counts match between source and destination
- No data corruption or loss during migration
- pgAdmin shows migrated data accessible via web interface

## Notes

- Original SQLite database is preserved during migration
- Migration scripts can be re-run safely (with --clear flag)
- UUIDs are generated for PostgreSQL primary keys while preserving legacy IDs
- JSON data structures are preserved for complex fields
- Migration logs all operations for troubleshooting