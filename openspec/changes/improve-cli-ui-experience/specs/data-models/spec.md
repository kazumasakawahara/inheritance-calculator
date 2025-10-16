# Data Models Specification - Contact Information Extension

## MODIFIED Requirements

### Requirement: Person Data Model
The Person model SHALL represent individuals in inheritance calculations with basic information, status, and optional contact information.

#### Scenario: Person creation with all fields
- **WHEN** creating a Person instance with full information
- **THEN** the system accepts:
  - Required: `name` (str)
  - Optional: `is_alive` (bool, default True)
  - Optional: `is_decedent` (bool, default False)
  - Optional: `birth_date` (date)
  - Optional: `death_date` (date)
  - Optional: `gender` (Gender enum)
  - Optional: `died_before_division` (bool, default False)
  - **NEW**: `address` (str, optional) - Physical address
  - **NEW**: `phone` (str, optional) - Phone number
  - **NEW**: `email` (str, optional) - Email address

#### Scenario: Person creation with legacy data (backward compatibility)
- **WHEN** creating a Person instance without contact fields
- **THEN** the system:
  - Accepts creation without `address`, `phone`, `email`
  - Sets contact fields to None
  - Maintains full functionality
  - No validation errors

#### Scenario: Person with contact information
- **WHEN** creating a Person with contact information
- **THEN** the system validates:
  - Email format if provided (must contain @ and domain)
  - Phone accepts any string (flexible for international formats)
  - Address accepts any string
  - All contact fields are optional
  - Invalid email format raises ValidationError

#### Scenario: Person serialization with contact info
- **WHEN** serializing Person to JSON/dict
- **THEN** the output includes:
  - All original Person fields
  - Contact fields if not None:
    - `"address": "東京都渋谷区..."`
    - `"phone": "03-1234-5678"`
    - `"email": "example@example.com"`
  - Contact fields omitted or null if not provided

#### Scenario: Person deserialization from legacy data
- **WHEN** deserializing Person from JSON without contact fields
- **THEN** the system:
  - Successfully creates Person instance
  - Sets contact fields to None
  - No errors or warnings
  - Maintains backward compatibility with existing data

## ADDED Requirements

### Requirement: Contact Information Validation
The Person model SHALL validate contact information format when provided.

#### Scenario: Valid email format
- **WHEN** creating Person with email "user@example.com"
- **THEN** the validation succeeds

#### Scenario: Invalid email format
- **WHEN** creating Person with email "invalid-email"
- **THEN** the system raises:
  - ValidationError
  - Message contains "email" and "format"

#### Scenario: Phone number flexibility
- **WHEN** creating Person with any of these phone formats:
  - "03-1234-5678"
  - "0312345678"
  - "090-1234-5678"
  - "+81-3-1234-5678"
- **THEN** all formats are accepted without validation errors

#### Scenario: Address flexibility
- **WHEN** creating Person with address in any format
- **THEN** the system accepts:
  - Japanese address format
  - Multi-line addresses (with newlines)
  - Any character encoding (UTF-8)
  - No length limit (within reasonable bounds)
