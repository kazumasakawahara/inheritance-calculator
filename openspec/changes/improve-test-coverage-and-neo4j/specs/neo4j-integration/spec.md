# Neo4j Integration Specification Delta

## ADDED Requirements

### Requirement: Person Repository Operations
The system SHALL provide a PersonRepository with CRUD operations for managing Person nodes in Neo4j.

#### Scenario: Create person in Neo4j
- **GIVEN** a Person model with valid attributes
- **WHEN** calling PersonRepository.create(person)
- **THEN** a Person node SHALL be created in Neo4j
- **AND** the node SHALL have all person attributes as properties
- **AND** the created person SHALL be returned with Neo4j ID

#### Scenario: Find person by name
- **GIVEN** persons stored in Neo4j
- **WHEN** calling PersonRepository.find_by_name(name)
- **THEN** the matching Person SHALL be returned
- **AND** all attributes SHALL be populated correctly
- **AND** None SHALL be returned if not found

#### Scenario: Find decedent
- **GIVEN** persons stored in Neo4j with is_decedent flag
- **WHEN** calling PersonRepository.find_decedent()
- **THEN** the person with is_decedent=True SHALL be returned
- **AND** only one decedent SHALL exist per query

#### Scenario: Update person attributes
- **GIVEN** an existing Person in Neo4j
- **WHEN** calling PersonRepository.update(person)
- **THEN** the Person node SHALL be updated with new attributes
- **AND** the updated person SHALL be returned

#### Scenario: Delete person
- **GIVEN** an existing Person in Neo4j
- **WHEN** calling PersonRepository.delete(name)
- **THEN** the Person node and all relationships SHALL be removed
- **AND** deletion SHALL be idempotent

### Requirement: Relationship Repository Operations
The system SHALL provide a RelationshipRepository for managing relationships between Person nodes.

#### Scenario: Create parent-child relationship
- **GIVEN** two Person nodes in Neo4j
- **WHEN** calling RelationshipRepository.create_child_of(child_name, parent_name)
- **THEN** a CHILD_OF relationship SHALL be created
- **AND** relationship properties SHALL be set correctly
- **AND** the relationship SHALL be queryable

#### Scenario: Create spouse relationship
- **GIVEN** two Person nodes in Neo4j
- **WHEN** calling RelationshipRepository.create_spouse_of(person1_name, person2_name)
- **THEN** a bidirectional SPOUSE_OF relationship SHALL be created
- **AND** is_current property SHALL be set to True by default

#### Scenario: Create sibling relationship
- **GIVEN** two Person nodes in Neo4j
- **WHEN** calling RelationshipRepository.create_sibling_of(person1_name, person2_name, blood_type)
- **THEN** a bidirectional SIBLING_OF relationship SHALL be created
- **AND** blood_type property SHALL be set (full/half)

#### Scenario: Find children of person
- **GIVEN** parent-child relationships in Neo4j
- **WHEN** calling RelationshipRepository.find_children(parent_name)
- **THEN** all children SHALL be returned as Person objects
- **AND** children SHALL be ordered by birth_date

#### Scenario: Find spouse of person
- **GIVEN** spouse relationships in Neo4j
- **WHEN** calling RelationshipRepository.find_spouse(person_name)
- **THEN** current spouse SHALL be returned (is_current=True)
- **AND** None SHALL be returned if no current spouse

#### Scenario: Find siblings of person
- **GIVEN** sibling relationships in Neo4j
- **WHEN** calling RelationshipRepository.find_siblings(person_name)
- **THEN** all siblings SHALL be returned with blood_type information

### Requirement: Cypher Query Correctness
The system SHALL execute correct Cypher queries for inheritance-related graph traversals.

#### Scenario: Find heirs by rank
- **GIVEN** a decedent and family graph in Neo4j
- **WHEN** querying heirs by rank (first, second, third)
- **THEN** correct heirs SHALL be identified according to civil law
- **AND** queries SHALL respect is_alive status
- **AND** queries SHALL exclude renounced/disqualified persons

#### Scenario: Find substitution heirs
- **GIVEN** a deceased heir with descendants
- **WHEN** querying substitution heirs (代襲相続人)
- **THEN** correct descendants SHALL be identified
- **AND** unlimited substitution SHALL work for children
- **AND** one-generation substitution SHALL work for siblings

#### Scenario: Find retransfer heirs
- **GIVEN** an heir who died before estate division
- **WHEN** querying retransfer heirs (再転相続人)
- **THEN** the deceased heir's heirs SHALL be identified
- **AND** statutory share relationships SHALL be preserved

### Requirement: Transaction Management
The system SHALL provide transaction support for atomic multi-operation updates.

#### Scenario: Atomic family creation
- **GIVEN** multiple persons and relationships to create
- **WHEN** executing within a transaction
- **THEN** all operations SHALL succeed or all SHALL fail
- **AND** partial updates SHALL NOT be persisted on error

#### Scenario: Transaction rollback on error
- **GIVEN** a transaction with multiple operations
- **WHEN** an error occurs during execution
- **THEN** the transaction SHALL be rolled back automatically
- **AND** database state SHALL remain unchanged

#### Scenario: Nested transaction handling
- **GIVEN** nested transaction requirements
- **WHEN** beginning a transaction within a transaction
- **THEN** appropriate transaction semantics SHALL be maintained
- **AND** commit/rollback SHALL affect correct scope

### Requirement: Neo4j Service Integration
The system SHALL provide a Neo4jService that integrates repositories with business logic.

#### Scenario: Save inheritance case to Neo4j
- **GIVEN** a complete inheritance calculation result
- **WHEN** calling Neo4jService.save_case(result)
- **THEN** all persons SHALL be created in Neo4j
- **AND** all relationships SHALL be created
- **AND** calculation metadata SHALL be stored

#### Scenario: Load inheritance case from Neo4j
- **GIVEN** a saved inheritance case in Neo4j
- **WHEN** calling Neo4jService.load_case(case_id)
- **THEN** all persons SHALL be loaded correctly
- **AND** all relationships SHALL be loaded
- **AND** InheritanceResult SHALL be reconstructible

#### Scenario: Query inheritance history
- **GIVEN** multiple inheritance cases in Neo4j
- **WHEN** querying by decedent name or date
- **THEN** matching cases SHALL be returned
- **AND** results SHALL be ordered by date

### Requirement: Error Handling and Validation
The system SHALL handle Neo4j errors gracefully and provide meaningful error messages.

#### Scenario: Connection failure handling
- **GIVEN** Neo4j server is unavailable
- **WHEN** attempting database operations
- **THEN** a DatabaseException SHALL be raised
- **AND** the error message SHALL indicate connection failure
- **AND** the application SHALL not crash

#### Scenario: Constraint violation handling
- **GIVEN** Neo4j constraints (e.g., unique person names)
- **WHEN** attempting to violate constraints
- **THEN** a ValidationError SHALL be raised
- **AND** the error message SHALL describe the violation

#### Scenario: Query syntax error handling
- **GIVEN** an invalid Cypher query
- **WHEN** executing the query
- **THEN** a DatabaseException SHALL be raised
- **AND** the original Neo4j error SHALL be logged

### Requirement: Performance and Optimization
The system SHALL optimize Neo4j queries for performance with proper indexing and query patterns.

#### Scenario: Indexed lookups
- **GIVEN** Neo4j indexes on person names and is_decedent
- **WHEN** querying by these properties
- **THEN** queries SHALL use indexes
- **AND** query performance SHALL be acceptable (<100ms for simple queries)

#### Scenario: Batch operations
- **GIVEN** multiple persons to create
- **WHEN** using batch create operations
- **THEN** operations SHALL be executed in a single transaction
- **AND** performance SHALL be better than individual creates

#### Scenario: Query result caching
- **GIVEN** frequently accessed relationships
- **WHEN** querying the same data multiple times
- **THEN** appropriate caching strategies SHALL be used
- **AND** cache invalidation SHALL work correctly

## MODIFIED Requirements

なし（新規スペックのため、既存要件の変更なし）

## REMOVED Requirements

なし（新規スペックのため、削除する既存要件なし）
