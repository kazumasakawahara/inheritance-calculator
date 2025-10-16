# Testing Specification Delta

## ADDED Requirements

### Requirement: Test Coverage Target
The project SHALL maintain a minimum test coverage of 75% across all source code modules.

#### Scenario: Overall coverage meets target
- **GIVEN** all source code is implemented
- **WHEN** running pytest with coverage reporting
- **THEN** overall coverage SHALL be at least 75%

#### Scenario: Critical modules have higher coverage
- **GIVEN** core business logic modules (services, models)
- **WHEN** measuring module-specific coverage
- **THEN** critical modules SHALL have at least 85% coverage

### Requirement: Neo4j Repository Testing
The system SHALL provide comprehensive tests for Neo4j repository layer with both unit and integration tests.

#### Scenario: Repository unit tests with mocks
- **GIVEN** PersonRepository and RelationshipRepository implementations
- **WHEN** running unit tests with mocked Neo4j driver
- **THEN** all CRUD operations SHALL be tested
- **AND** all search operations SHALL be tested
- **AND** error handling SHALL be tested

#### Scenario: Repository integration tests with real Neo4j
- **GIVEN** a running Neo4j test instance
- **WHEN** running integration tests marked with @pytest.mark.integration
- **THEN** actual Cypher queries SHALL execute against real database
- **AND** data persistence SHALL be verified
- **AND** transactions SHALL be tested

#### Scenario: Optional integration test execution
- **GIVEN** integration tests require Neo4j instance
- **WHEN** Neo4j is not available
- **THEN** integration tests SHALL be skipped gracefully
- **AND** unit tests SHALL continue to execute

### Requirement: CLI Command Testing
The system SHALL test all CLI commands with comprehensive scenarios including success and error cases.

#### Scenario: Calculate command execution
- **GIVEN** valid input data (JSON or CSV)
- **WHEN** executing calculate command
- **THEN** correct inheritance shares SHALL be calculated
- **AND** results SHALL be displayed in specified format

#### Scenario: File input/output testing
- **GIVEN** various file formats (JSON, CSV)
- **WHEN** reading input files
- **THEN** data SHALL be parsed correctly
- **AND** validation errors SHALL be handled gracefully

#### Scenario: Error handling in commands
- **GIVEN** invalid input or system errors
- **WHEN** executing commands
- **THEN** user-friendly error messages SHALL be displayed
- **AND** exit codes SHALL indicate success or failure

### Requirement: Service Layer Test Coverage
Core service classes SHALL achieve at least 85% test coverage with focus on edge cases.

#### Scenario: Heir validator edge cases
- **GIVEN** complex inheritance scenarios
- **WHEN** validating heir qualifications
- **THEN** substitution inheritance cases SHALL be tested
- **AND** disqualification cases SHALL be tested
- **AND** disinheritance cases SHALL be tested

#### Scenario: Inheritance calculator edge cases
- **GIVEN** retransfer inheritance scenarios
- **WHEN** calculating shares
- **THEN** statutory share distribution SHALL be verified
- **AND** renunciation conflict validation SHALL be tested

### Requirement: Database Layer Test Coverage
Database layer SHALL achieve at least 85% test coverage including transaction management.

#### Scenario: Transaction management testing
- **GIVEN** database operations requiring transactions
- **WHEN** executing transactional operations
- **THEN** commit operations SHALL be tested
- **AND** rollback operations SHALL be tested
- **AND** nested transactions SHALL be tested

#### Scenario: Connection management testing
- **GIVEN** database connection lifecycle
- **WHEN** establishing and closing connections
- **THEN** connection pooling SHALL be tested
- **AND** connection error handling SHALL be tested
- **AND** reconnection logic SHALL be tested

### Requirement: Test Infrastructure
The project SHALL provide standardized test utilities, fixtures, and helpers.

#### Scenario: Shared test fixtures
- **GIVEN** common test data requirements
- **WHEN** writing tests across multiple modules
- **THEN** reusable fixtures SHALL be available
- **AND** fixtures SHALL be documented
- **AND** fixtures SHALL follow consistent naming

#### Scenario: Test data builders
- **GIVEN** complex domain objects (Person, Relationship)
- **WHEN** creating test data
- **THEN** builder pattern utilities SHALL be available
- **AND** builders SHALL support fluent API
- **AND** builders SHALL handle default values

#### Scenario: Assertion helpers
- **GIVEN** domain-specific assertions
- **WHEN** verifying test outcomes
- **THEN** custom assertion helpers SHALL be available
- **AND** assertion messages SHALL be descriptive

### Requirement: Test Organization
Tests SHALL be organized by layer and type with clear naming conventions.

#### Scenario: Test directory structure
- **GIVEN** project source code structure
- **WHEN** organizing tests
- **THEN** tests SHALL mirror source code structure
- **AND** test files SHALL be prefixed with `test_`
- **AND** test classes SHALL be prefixed with `Test`

#### Scenario: Test categorization
- **GIVEN** different types of tests
- **WHEN** running test suites
- **THEN** unit tests SHALL be marked appropriately
- **AND** integration tests SHALL be marked with @pytest.mark.integration
- **AND** slow tests SHALL be marked with @pytest.mark.slow

#### Scenario: Test execution strategies
- **GIVEN** different test execution needs
- **WHEN** running pytest
- **THEN** fast unit tests SHALL run by default
- **AND** integration tests SHALL run with --run-integration flag
- **AND** coverage SHALL be measurable per module

## MODIFIED Requirements

なし（新規スペックのため、既存要件の変更なし）

## REMOVED Requirements

なし（新規スペックのため、削除する既存要件なし）
