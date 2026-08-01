"""Migration: add 'active' column to t_tasks and t_habit_sops for existing databases.

Usage: python migrations/legacy/fix_active_column.py
Run this once after updating the code with the new 'active' field.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'app.db'

def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f'PRAGMA table_info({table})')
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

def main():
    if not DB_PATH.exists():
        print(f'❌ Database not found at {DB_PATH}')
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    changes = []

    # ── t_tasks ──
    if not column_exists(cursor, 't_tasks', 'active'):
        cursor.execute('ALTER TABLE t_tasks ADD COLUMN active INTEGER NOT NULL DEFAULT 1')
        changes.append('t_tasks')
        print('✅ Added active column to t_tasks')
    else:
        print('ℹ️  active column already exists in t_tasks')

    cnt = cursor.execute('UPDATE t_tasks SET active = 1 WHERE active IS NULL').rowcount
    if cnt:
        print(f'✅ Set active=1 for {cnt} tasks')

    # ── t_habit_sops ──
    if not column_exists(cursor, 't_habit_sops', 'active'):
        cursor.execute('ALTER TABLE t_habit_sops ADD COLUMN active INTEGER NOT NULL DEFAULT 1')
        changes.append('t_habit_sops')
        print('✅ Added active column to t_habit_sops')
    else:
        print('ℹ️  active column already exists in t_habit_sops')

    cnt = cursor.execute('UPDATE t_habit_sops SET active = 1 WHERE active IS NULL').rowcount
    if cnt:
        print(f'✅ Set active=1 for {cnt} habits')

    conn.commit()
    conn.close()

    if changes:
        print(f'\n🎉 Migration complete! Added columns to: {", ".join(changes)}')
    else:
        print('\n✨ No changes needed - database is up to date')

    print('\nPlease restart the backend server now.')

if __name__ == '__main__':
    main()
