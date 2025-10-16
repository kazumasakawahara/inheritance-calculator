# CLI Interface Capability Specification

## ADDED Requirements

### Requirement: Progress Indication for Long-Running Operations
The CLI SHALL display visual progress indicators during long-running operations to provide user feedback.

#### Scenario: Neo4j save with progress display
- **WHEN** user executes a command with `--save-to-neo4j` flag
- **THEN** the system displays a progress bar showing:
  - Current step name (e.g., "データ検証中", "Neo4j接続中", "人物ノード作成中")
  - Progress percentage (0-100%)
  - Elapsed time
  - Estimated time remaining (when calculable)

#### Scenario: CSV parsing with progress display
- **WHEN** user loads a large CSV file with 100+ rows
- **THEN** the system displays:
  - Parsing progress as rows processed
  - Current row number and total rows
  - Spinner animation during validation

#### Scenario: PDF generation with progress display
- **WHEN** user exports result to PDF format
- **THEN** the system displays:
  - Report generation steps (template loading, data rendering, PDF creation)
  - Progress indicator for each step
  - Completion notification with file path

### Requirement: Enhanced Interactive Prompts
The CLI SHALL provide improved interactive prompts with clear field descriptions, validation, pending capability, and modification capabilities.

#### Scenario: Optional field with default value
- **WHEN** user is prompted for an optional field (e.g., "被相続人の生年月日")
- **THEN** the system displays:
  - Field description and purpose
  - `[オプション]` label
  - Default value in brackets if applicable
  - Accept Enter key to skip or use default

#### Scenario: Pending (hold) input for unknown information
- **WHEN** user is prompted for information not yet known (e.g., "相続放棄者はいますか？")
- **THEN** the system displays:
  - Option to mark as "未確定" (pending/unknown)
  - Typing `pending`, `保留`, or `未確定` marks the field as pending
  - Pending fields are highlighted in yellow in confirmation screen
  - System continues without requiring immediate answer

#### Scenario: Real-time input validation
- **WHEN** user enters an invalid date format (e.g., "2025-13-45")
- **THEN** the system immediately displays:
  - Error message in red color
  - Expected format with example (e.g., "YYYY-MM-DD形式で入力してください (例: 2025-06-15)")
  - Re-prompt without clearing previous valid inputs

#### Scenario: Input confirmation with pending items highlighted
- **WHEN** user completes all input fields (including some marked as pending)
- **THEN** the system displays:
  - Summary table of all entered data
  - Pending items shown with yellow background and "[未確定]" label
  - Numbered list of fields
  - Prompt: "修正する項目の番号を入力してください（Enter で確定）"
- **AND WHEN** user enters a field number
- **THEN** the system re-prompts only for that specific field

#### Scenario: Update pending items on session resume
- **WHEN** user resumes a saved session with pending items
- **THEN** the system displays:
  - List of pending items with numbers
  - Prompt: "保留項目を更新しますか？ (y/n)"
  - **IF** yes, prompts for each pending item sequentially
  - **IF** no, continues with pending items unchanged
  - Option to update specific pending items by number

### Requirement: Visual Result Representation
The CLI SHALL provide visual representations of calculation results including ASCII art family trees and graphical share displays.

#### Scenario: ASCII art family tree display
- **WHEN** calculation result includes multiple heirs with different ranks
- **THEN** the system displays an ASCII art family tree showing:
  - Decedent at the top center with distinctive icon (👤 or ⚰️)
  - Spouse connected with marriage symbol (💑 or ═)
  - Children as branches below decedent
  - Parents as branches above decedent
  - Siblings as branches to the side
  - Color-coded by heritage rank (green for spouse, blue for first rank, yellow for second, magenta for third)

#### Scenario: Share percentage visualization
- **WHEN** displaying heir shares in result table
- **THEN** each heir row includes:
  - Fraction representation (e.g., "1/2")
  - Percentage (e.g., "50.00%")
  - Visual progress bar using `━` characters proportional to share
  - Color corresponding to heritage rank

#### Scenario: Summary panel with emphasis
- **WHEN** displaying calculation summary
- **THEN** the system shows:
  - Bordered panel with title "計算サマリー"
  - Key information with icons (👤 被相続人, 👨‍👩‍👧‍👦 相続人総数)
  - Warning/notice in highlighted yellow panel if applicable
  - Legal basis in cyan-colored section

### Requirement: Improved Error Messages and Help
The CLI SHALL provide actionable error messages with specific guidance and comprehensive help information.

#### Scenario: File not found error with guidance
- **WHEN** user specifies a non-existent input file
- **THEN** the system displays:
  - Error message: "ファイルが見つかりません: [path]"
  - Guidance: "以下を確認してください:"
  - Checklist of potential issues (path typo, working directory, file permissions)
  - Example of correct usage

#### Scenario: Invalid JSON format error with specific location
- **WHEN** JSON parsing fails at line 15
- **THEN** the system displays:
  - Error type and line number: "JSONエラー (15行目)"
  - Problematic content snippet
  - Expected structure or value
  - Link to JSON template documentation

#### Scenario: In-line help during interactive mode
- **WHEN** user types `?` during any interactive prompt
- **THEN** the system displays:
  - Field description and purpose
  - Valid values or format
  - Example inputs
  - Whether field is required or optional
- **AND** re-displays the prompt after help

### Requirement: Session Management
The CLI SHALL support session save/resume functionality to allow interrupting and continuing work.

#### Scenario: Save interrupted interactive session
- **WHEN** user presses Ctrl+C during interactive input mode
- **THEN** the system:
  - Displays: "セッションを保存しますか? (y/n)"
  - **IF** user enters 'y', saves current state to temporary file
  - Shows session ID and resume command
  - Exits gracefully with code 130

#### Scenario: Resume saved session
- **WHEN** user executes `inheritance-calculator resume [session-id]`
- **THEN** the system:
  - Loads saved session data
  - Displays summary of previously entered data
  - Prompts: "続きから再開しますか? (y/n)"
  - **IF** yes, continues from next unanswered field
  - **IF** no, shows modification menu

#### Scenario: List saved sessions
- **WHEN** user executes `inheritance-calculator sessions --list`
- **THEN** the system displays:
  - Table of saved sessions with columns:
    - Session ID
    - Created date/time
    - Progress percentage
    - Decedent name (if entered)
  - Commands to resume or delete each session

### Requirement: Command Shortcuts and Aliases
The CLI SHALL provide convenient shortcuts and aliases for common operations.

#### Scenario: Shortcut for interactive mode
- **WHEN** user executes `inheritance-calculator` with no arguments
- **THEN** the system:
  - Displays welcome header
  - Shows quick-start menu:
    1. 新規相続計算 (対話形式)
    2. ファイルから計算
    3. セッション再開
    4. デモ実行
    5. ヘルプ
  - Prompts user to select number

#### Scenario: Quick calculation from clipboard
- **WHEN** user executes `inheritance-calculator calc --from-clipboard`
- **THEN** the system:
  - Reads JSON data from system clipboard
  - Validates format
  - Executes calculation
  - Displays result

#### Scenario: Export to multiple formats in one command
- **WHEN** user executes `inheritance-calculator calc -i input.json -o result --formats json,md,pdf`
- **THEN** the system generates:
  - result.json
  - result.md
  - result.pdf
  - Displays success message for each format

### Requirement: Contact Information Collection for Confirmed Heirs
The CLI SHALL provide functionality to collect contact information (address, phone, email) for confirmed heirs after inheritance calculation.

#### Scenario: Contact information prompt after calculation
- **WHEN** inheritance calculation is completed and heirs are confirmed
- **THEN** the system displays:
  - Message: "相続人の連絡先情報を入力しますか？ (y/n)"
  - **IF** yes, prompts for each confirmed heir sequentially:
    - "【{heir_name}】の連絡先情報を入力してください"
    - Address prompt: "住所 [オプション]:"
    - Phone prompt: "電話番号 [オプション]:"
    - Email prompt: "メールアドレス [オプション]:"
  - All fields are optional and can be skipped with Enter key
  - Invalid email format triggers validation error and re-prompt

#### Scenario: Contact information validation
- **WHEN** user enters email address
- **THEN** the system validates:
  - Email format (contains @ and domain)
  - Displays error if invalid: "メールアドレスの形式が正しくありません"
- **WHEN** user enters phone number
- **THEN** the system accepts:
  - Japanese phone formats (e.g., "03-1234-5678", "090-1234-5678")
  - Hyphen-separated or continuous digits
  - No strict validation (flexible for various formats)

#### Scenario: Contact information in output reports
- **WHEN** user exports calculation result to PDF or Markdown
- **THEN** the report includes:
  - Contact information section for each heir (if provided)
  - Table format with columns: 氏名, 住所, 電話番号, メールアドレス
  - Empty fields shown as "-" or blank
  - Contact section omitted if no contact info was collected

#### Scenario: Contact information persistence in Neo4j
- **WHEN** user saves result to Neo4j with `--save-to-neo4j` flag
- **THEN** the system:
  - Saves contact information to Person nodes as properties
  - Properties: `address`, `phone`, `email` (all optional)
  - Null values for empty contact fields
  - Can retrieve contact info when loading from Neo4j

#### Scenario: Skip contact information collection
- **WHEN** user chooses not to enter contact information
- **THEN** the system:
  - Skips all contact prompts
  - Proceeds directly to result display or next action
  - Contact fields remain null/empty in Person model
  - No contact section in output reports

### Requirement: Accessibility and Localization Support
The CLI SHALL support colorblind-friendly display modes and maintain full Japanese language support.

#### Scenario: Colorblind-friendly mode
- **WHEN** user sets environment variable `COLOR_MODE=accessible`
- **THEN** the system uses:
  - High-contrast color combinations
  - Pattern fills in addition to colors (e.g., ▓▓ vs ▒▒ vs ░░)
  - Icon/emoji indicators in addition to color coding
  - Maintains full functionality

#### Scenario: No-color mode for piping
- **WHEN** user sets `NO_COLOR=1` or pipes output (`| less`)
- **THEN** the system:
  - Disables all ANSI color codes
  - Uses plain text formatting
  - Preserves table structure with ASCII borders
  - Maintains readability

#### Scenario: Consistent Japanese terminology
- **WHEN** displaying any UI text, errors, or help messages
- **THEN** the system uses:
  - Consistent legal terminology (e.g., always "被相続人", never mixed terms)
  - Natural Japanese phrasing
  - Appropriate politeness level (です/ます form)
  - No direct English technical terms except in option names
