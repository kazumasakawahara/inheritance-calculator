# inheritance-calculation Specification

## Purpose
TBD - created by archiving change fix-retransfer-calculation. Update Purpose after archive.
## Requirements
### Requirement: Retransfer Inheritance Calculation
When an heir dies before estate division (再転相続), the system SHALL calculate the distribution of the deceased heir's share to their heirs according to Japanese Civil Code Article 896 and statutory share rules (Article 900).

The deceased heir's share SHALL be distributed to their heirs (spouse, children, lineal ascendants, or siblings) based on their **statutory inheritance shares**, NOT by equal division.

#### Scenario: Spouse and one child as retransfer heirs
- **GIVEN** decedent A dies in January 2025
- **AND** A's child B dies in February 2025 before estate division
- **AND** B has spouse C (alive) and child D (alive)
- **WHEN** calculating final inheritance shares
- **THEN** B's share (100%) SHALL be distributed as follows:
  - C (spouse): 50% of B's share (Civil Code Article 900-1: spouse 1/2)
  - D (child): 50% of B's share (Civil Code Article 900-1: children 1/2)

#### Scenario: Spouse and multiple children as retransfer heirs
- **GIVEN** decedent A dies in January 2025
- **AND** A's child B dies in February 2025 before estate division
- **AND** B has spouse C (alive), child D (alive), and child E (alive)
- **WHEN** calculating final inheritance shares
- **THEN** B's share (100%) SHALL be distributed as follows:
  - C (spouse): 50% of B's share (Civil Code Article 900-1: spouse 1/2)
  - D (child): 25% of B's share (Civil Code Article 900-1: children 1/2 divided by 2)
  - E (child): 25% of B's share (Civil Code Article 900-1: children 1/2 divided by 2)

#### Scenario: Mixed case - surviving spouse with retransfer heir
- **GIVEN** decedent A dies in January 2025
- **AND** A has spouse S (alive) and child B
- **AND** B dies in February 2025 before estate division
- **AND** B has child C (alive)
- **WHEN** calculating final inheritance shares
- **THEN** the distribution SHALL be:
  - S: 50% of A's estate (spouse share)
  - C: 50% of A's estate (inherits B's 50% child share via retransfer)

#### Scenario: No retransfer when heir is alive
- **GIVEN** decedent A dies in January 2025
- **AND** all heirs are alive at the time of estate division
- **WHEN** calculating inheritance shares
- **THEN** retransfer calculation SHALL NOT be applied
- **AND** normal statutory shares SHALL be used

#### Scenario: Multiple heirs die before division
- **GIVEN** decedent A dies in January 2025
- **AND** A has child B and child C
- **AND** both B and C die before estate division
- **AND** B has child D (alive)
- **AND** C has child E (alive)
- **WHEN** calculating final inheritance shares
- **THEN** B's share (50%) SHALL transfer to D (100% of B's share)
- **AND** C's share (50%) SHALL transfer to E (100% of C's share)
- **THEN** final distribution SHALL be:
  - D: 50% of A's estate
  - E: 50% of A's estate

### Requirement: Retransfer Heir Identification
The system SHALL identify retransfer heirs by determining the statutory heirs of the deceased heir according to inheritance rank rules (Articles 887-890).

#### Scenario: Identify spouse and children as retransfer heirs
- **GIVEN** heir B dies before estate division
- **AND** B has spouse C and children D, E
- **WHEN** identifying retransfer heirs
- **THEN** the system SHALL identify:
  - C as spouse (always inherits)
  - D and E as first-rank heirs (children)

#### Scenario: Identify lineal ascendants when no children
- **GIVEN** heir B dies before estate division
- **AND** B has spouse C and parents F, M (no children)
- **WHEN** identifying retransfer heirs
- **THEN** the system SHALL identify:
  - C as spouse
  - F and M as second-rank heirs (lineal ascendants)

#### Scenario: Identify siblings when no children or ascendants
- **GIVEN** heir B dies before estate division
- **AND** B has spouse C and sibling S (no children, no living parents)
- **WHEN** identifying retransfer heirs
- **THEN** the system SHALL identify:
  - C as spouse
  - S as third-rank heir (sibling)

### Requirement: Retransfer Calculation Basis Recording
The system SHALL record the legal basis for retransfer inheritance calculations in the calculation results.

#### Scenario: Record Civil Code Article 896
- **GIVEN** retransfer inheritance occurs
- **WHEN** generating calculation results
- **THEN** the calculation_basis SHALL include "民法第896条（相続人の相続、再転相続）"

#### Scenario: Record statutory share articles for retransfer heirs
- **GIVEN** retransfer inheritance to spouse and children
- **WHEN** generating calculation results
- **THEN** the calculation_basis SHALL include "民法第900条1号（配偶者1/2、子1/2）"

