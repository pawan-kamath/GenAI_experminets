# Foreign Key Enhancement Documentation

## Overview
The `utils.py` file has been enhanced to include foreign key relationship information for PostgreSQL databases. This enhancement provides the AI assistant with crucial relationship context when generating SQL queries.

## New Functions Added

### 1. `get_foreign_key_constraints(conn, db_type, schema_name="")`
- **Purpose**: Retrieves foreign key constraints for a PostgreSQL schema
- **Returns**: List of dictionaries containing FK constraint details
- **PostgreSQL Only**: Returns empty list for other database types

### 2. `get_foreign_key_relationships(conn, db_type, schema_name="")`
- **Purpose**: Returns formatted string of FK relationships for easy AI consumption
- **Returns**: Human-readable string describing all FK relationships
- **PostgreSQL Only**: Returns informative message for other database types

## Enhanced Function

### `get_database_schema(conn, db_type, schema="")`
- **Enhancement**: Now includes foreign key information for PostgreSQL databases
- **New Output Includes**:
  - Foreign key constraints for each table
  - Summary of all FK relationships at the end
- **Backward Compatible**: Existing functionality unchanged for SQLite

## Database Schema Output Format

### Before Enhancement
```
Table: customer
Columns:
  uuid varchar (Nullable: NO, Max Length: None)
  name varchar (Nullable: YES, Max Length: 255)
  config_uuid varchar (Nullable: YES, Max Length: None)
```

### After Enhancement
```
Table: customer
Columns:
  uuid varchar (Nullable: NO, Max Length: None)
  name varchar (Nullable: YES, Max Length: 255)
  config_uuid varchar (Nullable: YES, Max Length: None)
Foreign Keys:
  config_uuid -> config.uuid (Constraint: customer_config_fk)
  created_by -> user.uuid (Constraint: customer_creator_fk)

=== Foreign Key Relationships Summary ===
customer.config_uuid -> config.uuid
customer.created_by -> user.uuid
document.policy_uuid -> policy.uuid
...
```

## Usage Examples

### Basic Schema with FK Information
```python
conn = connect_db('postgresql', credentials)
schema_info = get_database_schema(conn, 'postgresql', 'genesis_v2')
# Now includes FK relationships automatically
```

### Get Only FK Relationships
```python
fk_info = get_foreign_key_relationships(conn, 'postgresql', 'genesis_v2')
print(fk_info)
```

### Get Raw FK Constraint Data
```python
fk_constraints = get_foreign_key_constraints(conn, 'postgresql', 'genesis_v2')
for fk in fk_constraints:
    print(f"{fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
```

## AI Assistant Benefits

With this enhancement, the AI assistant now has access to:

1. **Relationship Context**: Understanding which tables are related
2. **Join Query Assistance**: Can suggest proper JOIN conditions
3. **Data Integrity Awareness**: Knows which fields reference other tables
4. **Better Query Suggestions**: Can recommend related tables for complex queries

## Implementation Notes

- **PostgreSQL Specific**: FK functionality only works with PostgreSQL databases
- **Schema Required**: PostgreSQL connections must specify a schema name
- **Error Handling**: Gracefully handles connection errors and missing schemas
- **Performance**: Uses efficient queries to fetch FK information
- **Compatibility**: Maintains backward compatibility with existing code

## Testing

Use the provided `test_fk_functionality.py` script to verify the implementation:

```bash
cd /path/to/database_assistant
python test_fk_functionality.py
```

## Integration with Database Assistant

The enhanced schema information is automatically included in:
- AI assistant prompts (line 134 & 410 in app.py)
- Function calling descriptions
- Error correction contexts

This provides the AI with comprehensive database relationship knowledge for better query generation and assistance.
